# Architecture and design decisions

## Overview

A single FastAPI service exposes a small FHIR R4-style API and serves a static accessible web page.

```
Browser (HTML, CSS, vanilla JS)  ->  FastAPI (app/main.py)  ->  SQLAlchemy  ->  SQLite (default) or PostgreSQL
                                          |
                                          +-- app/security.py   API key roles: patient, clinician
                                          +-- app/schemas.py    request validation (Pydantic)
                                          +-- app/scoring.py    scoring and review rules
                                          +-- app/fhir.py       row <-> FHIR JSON, OperationOutcome errors
```

## FHIR usage

| Resource | Operations |
|---|---|
| `Questionnaire` | read (`GET /fhir/Questionnaire/rehab-check-1`) |
| `QuestionnaireResponse` | create (POST), read by id, search by `subject` |
| `OperationOutcome` | returned for every error |
| `Bundle` (searchset) | returned by the search |

Only the subset needed here is implemented. There is no capability statement, no `_include`,
no versioning, no paging, and no conformance testing against a FHIR validator. Total score and
the review flag are returned as extensions with example URLs, not registered profiles.

## Data model

One table, `questionnaire_responses`: id (UUID), pseudonymous patient reference, questionnaire id,
authored timestamp (UTC), answers (JSON), total score, review flag. Indexed on patient and time.

## Security decisions

- Role-based API keys, compared with `secrets.compare_digest`. Patients can submit; only clinicians can read.
- Strict input validation: fixed patient-id pattern (`[A-Za-z0-9-]{1,64}`), allowed answer range,
  required and unique items, size limits.
- No personal identifiers are stored; patients are pseudonymous references.
- Security headers (CSP, `nosniff`, `X-Frame-Options`, `no-store`).
- The front end writes to the DOM with `textContent` only, never `innerHTML`.
- Errors never echo stack traces.

## Known limitations (and what production would need)

| Limitation | Production approach |
|---|---|
| API keys are shared per role, not per user or patient | NHS-approved identity (for example NHS login) with OAuth 2.0 / OpenID Connect and per-patient authorisation |
| No audit log | Immutable audit trail of reads and writes |
| No encryption at rest configured | Managed database encryption, key management |
| Demo thresholds are not clinically validated | Clinical safety case and validated instruments |
| Not assessed against UK GDPR, DTAC, DCB0129/DCB0160 or medical device regulation | Formal data protection impact assessment, clinical risk management, regulatory assessment |
| Tested with SQLite; PostgreSQL configuration provided but not part of CI | Add a PostgreSQL service to CI |
| No rate limiting | Gateway or middleware rate limiting |

## Accessibility

Semantic HTML, labelled inputs, fieldset and legend groups for each question, skip link, visible
focus, live-region status messages, a data table alongside the chart, and colour not used alone.
It has been checked by hand, not audited against WCAG 2.2.
