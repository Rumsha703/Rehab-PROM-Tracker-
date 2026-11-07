"""The demo questionnaire, expressed as a FHIR R4 Questionnaire resource.

This is an invented five-item check for demonstration. It is NOT a validated clinical
instrument and must not be used for real patient care.
"""

QUESTIONNAIRE_ID = "rehab-check-1"
MIN_ANSWER = 0
MAX_ANSWER = 4

ITEMS = [
    ("q1", "How much pain did you have during your exercises this week?"),
    ("q2", "How difficult was it to walk on level ground?"),
    ("q3", "How difficult was it to climb stairs?"),
    ("q4", "How difficult was it to get in and out of a chair?"),
    ("q5", "How much did your condition limit your daily activities?"),
]
LINK_IDS = [link_id for link_id, _ in ITEMS]
MAX_SCORE = MAX_ANSWER * len(ITEMS)


def questionnaire_resource() -> dict:
    return {
        "resourceType": "Questionnaire",
        "id": QUESTIONNAIRE_ID,
        "status": "draft",
        "title": "Rehabilitation progress check (demo, not a validated instrument)",
        "subjectType": ["Patient"],
        "item": [
            {
                "linkId": link_id,
                "text": text,
                "type": "choice",
                "required": True,
                "answerOption": [{"valueInteger": v} for v in range(MIN_ANSWER, MAX_ANSWER + 1)],
            }
            for link_id, text in ITEMS
        ],
    }
