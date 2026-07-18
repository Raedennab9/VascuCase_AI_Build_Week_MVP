import pytest

from vascucase.cases import CASES
from vascucase.scoring import performance_band, score_case


def expert_answers(case):
    answers = {}
    for stage in case.stages:
        correct_for_stage = next(
            option.option_id
            for option in stage.question.options
            if option.option_id in case.correct_actions
        )
        answers[stage.question.question_id] = correct_for_stage
    return answers


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.case_id)
def test_every_case_expert_path_scores_100(case):
    result = score_case(case, expert_answers(case))

    assert result["score"] == 100
    assert result["band"] == "Excellent"
    assert result["critical_omissions"] == []
    assert result["unsafe_selections"] == []
    assert sum(item["score"] for item in result["domain_scores"].values()) == 100


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.case_id)
def test_every_case_flags_a_critical_omission(case):
    answers = expert_answers(case)
    critical_id = case.critical_actions[0]
    stage = next(
        stage
        for stage in case.stages
        if critical_id in {option.option_id for option in stage.question.options}
    )
    del answers[stage.question.question_id]

    result = score_case(case, answers)

    assert case.option_labels[critical_id] in result["critical_omissions"]
    assert result["score"] < 100


UNSAFE_CASES = [
    (case, option_id)
    for case in CASES
    for option_id in case.unsafe_choices
]


@pytest.mark.parametrize(
    ("case", "unsafe_id"),
    UNSAFE_CASES,
    ids=[f"{case.case_id}-{option_id}" for case, option_id in UNSAFE_CASES],
)
def test_every_explicit_unsafe_option_is_flagged(case, unsafe_id):
    answers = expert_answers(case)
    stage = next(
        stage
        for stage in case.stages
        if unsafe_id in {option.option_id for option in stage.question.options}
    )
    answers[stage.question.question_id] = unsafe_id

    result = score_case(case, answers)

    unsafe = next(item for item in result["unsafe_selections"] if item["action"] == case.option_labels[unsafe_id])
    assert unsafe["explanation"] == case.unsafe_choices[unsafe_id].explanation
    assert unsafe["penalty"] == case.unsafe_choices[unsafe_id].penalty
    assert result["score"] < 100


@pytest.mark.parametrize(
    ("score", "expected"),
    [(100, "Excellent"), (90, "Excellent"), (89, "Good"), (75, "Good"), (74, "Developing"), (60, "Developing"), (59, "Needs improvement"), (0, "Needs improvement")],
)
def test_consistent_performance_bands(score, expected):
    assert performance_band(score) == expected
