"""Settings read from environment variables.

The default API keys are for local development only. Set real values in any shared environment.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    patient_api_key: str
    clinician_api_key: str


def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./prom.db"),
        patient_api_key=os.getenv("PATIENT_API_KEY", "dev-patient-key"),
        clinician_api_key=os.getenv("CLINICIAN_API_KEY", "dev-clinician-key"),
    )
