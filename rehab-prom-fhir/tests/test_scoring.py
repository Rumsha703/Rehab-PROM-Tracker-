import pytest

from app import scoring


@pytest.mark.parametrize(
    ("answers", "expected"),
    [
        ({"q1": 0, "q2": 0, "q3": 0, "q4": 0, "q5": 0}, 0),
        ({"q1": 1, "q2": 2, "q3": 3, "q4": 2, "q5": 1}, 9),
        ({"q1": 4, "q2": 4, "q3": 4, "q4": 4, "q5": 4}, 20),
    ],
)
def test_total_score(answers, expected):
    assert scoring.total_score(answers) == expected


def test_review_on_high_total():
    assert scoring.needs_review({"q1": 3, "q2": 3, "q3": 2, "q4": 2, "q5": 2}, None)


def test_review_on_single_maximum_answer():
    assert scoring.needs_review({"q1": 4, "q2": 0, "q3": 0, "q4": 0, "q5": 0}, None)


def test_review_on_sharp_rise():
    answers = {"q1": 2, "q2": 2, "q3": 1, "q4": 1, "q5": 1}  # total 7
    assert scoring.needs_review(answers, previous_total=3)
    assert not scoring.needs_review(answers, previous_total=5)


def test_no_review_for_low_stable_scores():
    assert not scoring.needs_review({"q1": 1, "q2": 1, "q3": 1, "q4": 1, "q5": 1}, 5)


@pytest.mark.parametrize(
    ("totals", "expected"),
    [
        ([], "insufficient_data"),
        ([5], "insufficient_data"),
        ([8, 5], "improving"),
        ([5, 8], "worsening"),
        ([5, 5], "stable"),
    ],
)
def test_trend(totals, expected):
    assert scoring.trend(totals) == expected
