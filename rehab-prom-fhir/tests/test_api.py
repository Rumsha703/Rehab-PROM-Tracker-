from .conftest import CLINICIAN, PATIENT, make_payload

URL = "/fhir/QuestionnaireResponse"


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_questionnaire_has_five_required_items(client):
    q = client.get("/fhir/Questionnaire/rehab-check-1").json()
    assert q["resourceType"] == "Questionnaire"
    assert len(q["item"]) == 5
    assert all(i["required"] for i in q["item"])


def test_unknown_questionnaire_404(client):
    r = client.get("/fhir/Questionnaire/nope")
    assert r.status_code == 404
    assert r.json()["resourceType"] == "OperationOutcome"


def test_create_response_returns_201_location_and_score(client):
    r = client.post(URL, json=make_payload(values=(1, 2, 3, 2, 1)), headers=PATIENT)
    assert r.status_code == 201
    body = r.json()
    assert r.headers["location"].endswith(body["id"])
    assert body["resourceType"] == "QuestionnaireResponse"
    assert body["extension"][0]["valueInteger"] == 9


def test_missing_api_key_401(client):
    assert client.post(URL, json=make_payload()).status_code == 401


def test_wrong_api_key_401(client):
    r = client.post(URL, json=make_payload(), headers={"X-API-Key": "wrong"})
    assert r.status_code == 401


def test_unknown_link_id_422_operation_outcome(client):
    p = make_payload()
    p["item"][0]["linkId"] = "zzz"
    r = client.post(URL, json=p, headers=PATIENT)
    assert r.status_code == 422
    assert r.json()["resourceType"] == "OperationOutcome"


def test_answer_out_of_range_422(client):
    r = client.post(URL, json=make_payload(values=(5, 1, 1, 1, 1)), headers=PATIENT)
    assert r.status_code == 422


def test_missing_item_422(client):
    p = make_payload()
    p["item"].pop()
    assert client.post(URL, json=p, headers=PATIENT).status_code == 422


def test_duplicate_item_422(client):
    p = make_payload()
    p["item"][1]["linkId"] = "q1"
    assert client.post(URL, json=p, headers=PATIENT).status_code == 422


def test_bad_patient_reference_rejected(client):
    r = client.post(URL, json=make_payload(patient="a/../b<script>"), headers=PATIENT)
    assert r.status_code == 422


def test_wrong_status_rejected(client):
    p = make_payload()
    p["status"] = "in-progress"
    assert client.post(URL, json=p, headers=PATIENT).status_code == 422


def test_patient_key_cannot_read_responses(client):
    created = client.post(URL, json=make_payload(), headers=PATIENT).json()
    assert client.get(f"{URL}/{created['id']}", headers=PATIENT).status_code == 403
    assert client.get(f"{URL}?subject=Patient/demo-001", headers=PATIENT).status_code == 403


def test_clinician_reads_by_id(client):
    created = client.post(URL, json=make_payload(), headers=PATIENT).json()
    r = client.get(f"{URL}/{created['id']}", headers=CLINICIAN)
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_clinician_unknown_id_404(client):
    assert client.get(f"{URL}/does-not-exist", headers=CLINICIAN).status_code == 404


def test_search_by_subject_returns_bundle_for_that_patient_only(client):
    client.post(URL, json=make_payload("p-1"), headers=PATIENT)
    client.post(URL, json=make_payload("p-1"), headers=PATIENT)
    client.post(URL, json=make_payload("p-2"), headers=PATIENT)
    r = client.get(f"{URL}?subject=Patient/p-1", headers=CLINICIAN)
    assert r.status_code == 200
    assert r.json()["total"] == 2


def test_search_requires_valid_subject(client):
    assert client.get(f"{URL}?subject=bad", headers=CLINICIAN).status_code == 422


def test_summary_trend_and_review_flag(client):
    client.post(URL, json=make_payload("p-9", (3, 2, 2, 2, 2)), headers=PATIENT)  # 11
    client.post(URL, json=make_payload("p-9", (1, 1, 1, 1, 1)), headers=PATIENT)  # 5
    s = client.get("/api/patients/p-9/summary", headers=CLINICIAN).json()
    assert s["responses"] == 2
    assert s["trend"] == "improving"
    assert s["latest_needs_review"] is False


def test_summary_flags_high_score(client):
    client.post(URL, json=make_payload("p-8", (3, 3, 3, 3, 3)), headers=PATIENT)
    s = client.get("/api/patients/p-8/summary", headers=CLINICIAN).json()
    assert s["latest_needs_review"] is True


def test_summary_requires_clinician(client):
    assert client.get("/api/patients/p-8/summary", headers=PATIENT).status_code == 403


def test_summary_empty_patient(client):
    s = client.get("/api/patients/nobody/summary", headers=CLINICIAN).json()
    assert s["responses"] == 0
    assert s["trend"] == "insufficient_data"


def test_security_headers_present(client):
    h = client.get("/health").headers
    assert h["x-content-type-options"] == "nosniff"
    assert h["x-frame-options"] == "DENY"
    assert "default-src 'self'" in h["content-security-policy"]


def test_frontend_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Rehab PROM tracker" in r.text
