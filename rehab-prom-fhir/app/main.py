"""FastAPI application: FHIR-style QuestionnaireResponse capture and a clinician summary."""

import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi import Path as PathParam
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import fhir, scoring
from .db import Base, engine, get_db
from .models import ResponseRow
from .questionnaire import (
    LINK_IDS,
    MAX_ANSWER,
    MIN_ANSWER,
    QUESTIONNAIRE_ID,
    questionnaire_resource,
)
from .schemas import PATIENT_REF, QuestionnaireResponseIn
from .security import current_role, require_clinician

FHIR_JSON = "application/fhir+json"
STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Rehab PROM tracker",
    version="1.0.0",
    description="Demo API. Not a medical device. Do not use with real patient data.",
    lifespan=lifespan,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    if not request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; frame-ancestors 'none'"
        )
    return response


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    messages = "; ".join(
        f"{'.'.join(str(p) for p in e['loc'][1:])}: {e['msg']}" for e in exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content=fhir.operation_outcome("error", "invalid", messages),
        media_type=FHIR_JSON,
    )


@app.exception_handler(HTTPException)
async def http_handler(_: Request, exc: HTTPException):
    code = {401: "login", 403: "forbidden", 404: "not-found"}.get(exc.status_code, "processing")
    return JSONResponse(
        status_code=exc.status_code,
        content=fhir.operation_outcome("error", code, str(exc.detail)),
        media_type=FHIR_JSON,
        headers=exc.headers,
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/fhir/Questionnaire/{questionnaire_id}")
def read_questionnaire(questionnaire_id: str):
    if questionnaire_id != QUESTIONNAIRE_ID:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    return JSONResponse(questionnaire_resource(), media_type=FHIR_JSON)


def _validate_answers(payload: QuestionnaireResponseIn) -> dict[str, int]:
    if payload.questionnaire != f"Questionnaire/{QUESTIONNAIRE_ID}":
        raise HTTPException(status_code=422, detail="Unknown questionnaire")
    answers: dict[str, int] = {}
    for item in payload.item:
        if item.linkId not in LINK_IDS:
            raise HTTPException(status_code=422, detail=f"Unknown linkId {item.linkId}")
        if item.linkId in answers:
            raise HTTPException(status_code=422, detail=f"Duplicate linkId {item.linkId}")
        value = item.answer[0].valueInteger
        if not MIN_ANSWER <= value <= MAX_ANSWER:
            raise HTTPException(
                status_code=422,
                detail=f"{item.linkId} must be between {MIN_ANSWER} and {MAX_ANSWER}",
            )
        answers[item.linkId] = value
    missing = [k for k in LINK_IDS if k not in answers]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing answers: {', '.join(missing)}")
    return {k: answers[k] for k in LINK_IDS}


def _previous_total(db: Session, patient_ref: str) -> int | None:
    stmt = (
        select(ResponseRow.total_score)
        .where(ResponseRow.patient_ref == patient_ref)
        .order_by(ResponseRow.authored.desc())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


@app.post("/fhir/QuestionnaireResponse", status_code=201)
def create_response(
    payload: QuestionnaireResponseIn,
    db: Annotated[Session, Depends(get_db)],
    _role: Annotated[str, Depends(current_role)],
):
    answers = _validate_answers(payload)
    patient_ref = PATIENT_REF.match(payload.subject.reference).group(1)
    row = ResponseRow(
        id=str(uuid.uuid4()),
        patient_ref=patient_ref,
        questionnaire_id=QUESTIONNAIRE_ID,
        authored=datetime.now(UTC),
        answers=answers,
        total_score=scoring.total_score(answers),
        needs_review=scoring.needs_review(answers, _previous_total(db, patient_ref)),
    )
    db.add(row)
    db.commit()
    return JSONResponse(
        fhir.response_resource(row),
        status_code=201,
        media_type=FHIR_JSON,
        headers={"Location": f"/fhir/QuestionnaireResponse/{row.id}"},
    )


@app.get("/fhir/QuestionnaireResponse/{response_id}")
def read_response(
    response_id: str,
    db: Annotated[Session, Depends(get_db)],
    _role: Annotated[str, Depends(require_clinician)],
):
    row = db.get(ResponseRow, response_id)
    if row is None:
        raise HTTPException(status_code=404, detail="QuestionnaireResponse not found")
    return JSONResponse(fhir.response_resource(row), media_type=FHIR_JSON)


@app.get("/fhir/QuestionnaireResponse")
def search_responses(
    db: Annotated[Session, Depends(get_db)],
    _role: Annotated[str, Depends(require_clinician)],
    subject: Annotated[str, Query(pattern=r"^Patient/[A-Za-z0-9-]{1,64}$")],
):
    patient_ref = subject.split("/", 1)[1]
    rows = (
        db.execute(
            select(ResponseRow)
            .where(ResponseRow.patient_ref == patient_ref)
            .order_by(ResponseRow.authored)
        )
        .scalars()
        .all()
    )
    bundle = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(rows),
        "entry": [{"resource": fhir.response_resource(r)} for r in rows],
    }
    return JSONResponse(bundle, media_type=FHIR_JSON)


@app.get("/api/patients/{patient_id}/summary")
def patient_summary(
    patient_id: Annotated[str, PathParam(pattern=r"^[A-Za-z0-9-]{1,64}$")],
    db: Annotated[Session, Depends(get_db)],
    _role: Annotated[str, Depends(require_clinician)],
):
    rows = (
        db.execute(
            select(ResponseRow)
            .where(ResponseRow.patient_ref == patient_id)
            .order_by(ResponseRow.authored)
        )
        .scalars()
        .all()
    )
    totals = [r.total_score for r in rows]
    return {
        "patient": patient_id,
        "responses": len(rows),
        "series": [
            {
                "authored": r.authored.isoformat(),
                "total": r.total_score,
                "needs_review": r.needs_review,
            }
            for r in rows
        ],
        "trend": scoring.trend(totals),
        "latest_needs_review": bool(rows and rows[-1].needs_review),
    }


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
