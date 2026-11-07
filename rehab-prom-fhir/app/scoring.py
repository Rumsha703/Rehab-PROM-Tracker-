"""Scoring rules. Higher scores mean more difficulty.

The thresholds are demonstration values chosen for this project. They are not clinically validated.
"""

from .questionnaire import MAX_ANSWER

REVIEW_TOTAL_THRESHOLD = 12
REVIEW_JUMP_THRESHOLD = 4


def total_score(answers: dict[str, int]) -> int:
    return sum(answers.values())


def needs_review(answers: dict[str, int], previous_total: int | None) -> bool:
    """Flag for clinician review on a high total, a maximum single answer, or a sharp rise."""
    total = total_score(answers)
    if total >= REVIEW_TOTAL_THRESHOLD:
        return True
    if any(v == MAX_ANSWER for v in answers.values()):
        return True
    return previous_total is not None and total - previous_total >= REVIEW_JUMP_THRESHOLD


def trend(totals: list[int]) -> str:
    """Compare the latest total with the one before it. Lower is better."""
    if len(totals) < 2:
        return "insufficient_data"
    if totals[-1] < totals[-2]:
        return "improving"
    if totals[-1] > totals[-2]:
        return "worsening"
    return "stable"
