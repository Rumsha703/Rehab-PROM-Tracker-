"""Request validation for an incoming FHIR QuestionnaireResponse (the subset this API supports)."""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

PATIENT_REF = re.compile(r"^Patient/([A-Za-z0-9-]{1,64})$")


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    valueInteger: int  # noqa: N815 (FHIR field name)


class ResponseItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    linkId: str = Field(max_length=32)  # noqa: N815
    answer: list[Answer] = Field(min_length=1, max_length=1)


class Subject(BaseModel):
    reference: str

    @field_validator("reference")
    @classmethod
    def valid_reference(cls, v: str) -> str:
        if not PATIENT_REF.match(v):
            raise ValueError("subject.reference must look like Patient/<pseudonymous-id>")
        return v


class QuestionnaireResponseIn(BaseModel):
    model_config = ConfigDict(extra="ignore")
    resourceType: str  # noqa: N815
    questionnaire: str
    status: str
    subject: Subject
    item: list[ResponseItem] = Field(max_length=50)

    @field_validator("resourceType")
    @classmethod
    def check_type(cls, v: str) -> str:
        if v != "QuestionnaireResponse":
            raise ValueError("resourceType must be QuestionnaireResponse")
        return v

    @field_validator("status")
    @classmethod
    def check_status(cls, v: str) -> str:
        if v != "completed":
            raise ValueError("only status 'completed' is accepted")
        return v
