import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app

PATIENT = {"X-API-Key": "dev-patient-key"}
CLINICIAN = {"X-API-Key": "dev-clinician-key"}


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_payload(patient="demo-001", values=(1, 1, 1, 1, 1)):
    return {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "questionnaire": "Questionnaire/rehab-check-1",
        "subject": {"reference": f"Patient/{patient}"},
        "item": [
            {"linkId": f"q{i + 1}", "answer": [{"valueInteger": v}]} for i, v in enumerate(values)
        ],
    }
