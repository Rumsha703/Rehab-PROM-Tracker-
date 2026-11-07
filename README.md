# Rehab PROM tracker (FHIR R4-style API)

A small full-stack demo for capturing **patient reported outcome measures (PROMs)** during
rehabilitation and giving a clinician a simple summary. Python, FastAPI, SQLAlchemy and a
dependency-free accessible web page.

> **Demo only. Not a medical device. Do not use with real patient data.** The questionnaire is an
> invented five-item example, not a validated clinical instrument, and the review thresholds are
> demonstration values.

**Project type:** personal portfolio project, built to learn and show full-stack and FHIR basics.
It has not been deployed in any NHS or commercial setting.

**AI-assisted development:** this project was built with the help of Claude (an AI coding assistant).
Generated code was reviewed, run, and covered by an automated test suite before publishing.

## Features

- FHIR R4-style endpoints: `Questionnaire` (read), `QuestionnaireResponse` (create, read, search), `OperationOutcome` errors, `Bundle` search results
- Server-side validation of every answer (known items, range 0 to 4, all items required, no duplicates)
- Scoring and a clinician review flag (high total, a maximum single answer, or a sharp rise)
- Role-based API keys: patients submit, clinicians read
- Clinician summary with trend and an accessible chart plus data table
- Security headers and DOM-safe front end
- OpenAPI documentation at `/docs`
- Automated tests, linting and a GitHub Actions workflow

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000 for the web page and http://localhost:8000/docs for the API.
Default development keys are `dev-patient-key` and `dev-clinician-key`. Set `PATIENT_API_KEY`,
`CLINICIAN_API_KEY` and `DATABASE_URL` in any shared environment.

## Run the tests

```bash
pytest --cov=app --cov-report=term-missing
ruff check .
```

## Example

```bash
curl -X POST http://localhost:8000/fhir/QuestionnaireResponse \
  -H "Content-Type: application/json" -H "X-API-Key: dev-patient-key" \
  -d '{"resourceType":"QuestionnaireResponse","status":"completed",
       "questionnaire":"Questionnaire/rehab-check-1",
       "subject":{"reference":"Patient/demo-001"},
       "item":[{"linkId":"q1","answer":[{"valueInteger":3}]},
               {"linkId":"q2","answer":[{"valueInteger":2}]},
               {"linkId":"q3","answer":[{"valueInteger":2}]},
               {"linkId":"q4","answer":[{"valueInteger":1}]},
               {"linkId":"q5","answer":[{"valueInteger":2}]}]}'

curl http://localhost:8000/api/patients/demo-001/summary -H "X-API-Key: dev-clinician-key"
```

## API

| Method and path | Role | Purpose |
|---|---|---|
| `GET /fhir/Questionnaire/rehab-check-1` | none | Read the questionnaire |
| `POST /fhir/QuestionnaireResponse` | patient or clinician | Submit answers (201 and `Location`) |
| `GET /fhir/QuestionnaireResponse/{id}` | clinician | Read one response |
| `GET /fhir/QuestionnaireResponse?subject=Patient/{id}` | clinician | Search a patient's responses |
| `GET /api/patients/{id}/summary` | clinician | Trend, series and review flag |
| `GET /health` | none | Health check |

## Docker (optional)

`docker compose up --build` starts the API with PostgreSQL. The compose and Docker configuration
are provided; the automated tests and CI use SQLite.

## Design and limitations

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for design decisions, security choices, and a clear
list of what a production NHS system would additionally require (identity, audit, UK GDPR, DTAC,
clinical safety, medical device regulation).

## Licence

MIT
