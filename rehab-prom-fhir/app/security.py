"""API key authentication with two roles.

This is deliberately simple: roles are not tied to individual patients. A production system
would use NHS-approved identity (for example NHS login or OAuth 2.0 / OpenID Connect) and
per-patient authorisation. See docs/ARCHITECTURE.md.
"""

import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException

from .config import Settings, get_settings


def current_role(
    x_api_key: Annotated[str | None, Header()] = None,
    settings: Annotated[Settings, Depends(get_settings)] = None,
) -> str:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    if secrets.compare_digest(x_api_key, settings.clinician_api_key):
        return "clinician"
    if secrets.compare_digest(x_api_key, settings.patient_api_key):
        return "patient"
    raise HTTPException(status_code=401, detail="Invalid API key")


def require_clinician(role: Annotated[str, Depends(current_role)]) -> str:
    if role != "clinician":
        raise HTTPException(status_code=403, detail="Clinician role required")
    return role
