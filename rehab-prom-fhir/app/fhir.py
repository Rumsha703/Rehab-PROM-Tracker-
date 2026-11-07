"""Mapping between database rows and FHIR-style JSON, plus OperationOutcome errors."""

from .models import ResponseRow
from .questionnaire import ITEMS, QUESTIONNAIRE_ID

SCORE_EXTENSION = "https://example.org/fhir/StructureDefinition/total-score"
REVIEW_EXTENSION = "https://example.org/fhir/StructureDefinition/needs-clinician-review"


def operation_outcome(severity: str, code: str, diagnostics: str) -> dict:
    return {
        "resourceType": "OperationOutcome",
        "issue": [{"severity": severity, "code": code, "diagnostics": diagnostics}],
    }


def response_resource(row: ResponseRow) -> dict:
    texts = dict(ITEMS)
    return {
        "resourceType": "QuestionnaireResponse",
        "id": row.id,
        "questionnaire": f"Questionnaire/{QUESTIONNAIRE_ID}",
        "status": "completed",
        "subject": {"reference": f"Patient/{row.patient_ref}"},
        "authored": row.authored.isoformat(),
        "item": [
            {"linkId": k, "text": texts[k], "answer": [{"valueInteger": v}]}
            for k, v in row.answers.items()
        ],
        "extension": [
            {"url": SCORE_EXTENSION, "valueInteger": row.total_score},
            {"url": REVIEW_EXTENSION, "valueBoolean": row.needs_review},
        ],
    }
