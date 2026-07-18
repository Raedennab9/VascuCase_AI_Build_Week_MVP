import random

import pytest
from pydantic import ValidationError

from vascucase.cases import CASES, CATEGORIES
from vascucase.cases.library import filter_cases, select_case
from vascucase.cases.schema import VascularCase


def test_library_has_eight_unique_validated_cases():
    assert len(CASES) == 8
    assert len({case.case_id for case in CASES}) == 8
    assert all(isinstance(case, VascularCase) for case in CASES)
    assert all(len(case.stages) == 4 for case in CASES)
    assert all(sum(case.scoring_weights.values()) == 100 for case in CASES)
    assert all(case.references and case.learning_points for case in CASES)
    assert all(case.fictional and not case.contains_real_patient_information for case in CASES)


def test_schema_rejects_missing_option_ids_and_non_100_point_rubrics():
    payload = CASES[0].model_dump(mode="python")
    payload["critical_actions"] = ["missing_option"]
    payload["scoring_weights"][CASES[0].correct_actions[0]] = 24

    with pytest.raises(ValidationError) as error:
        VascularCase.model_validate(payload)

    message = str(error.value)
    assert "Critical actions" in message or "100 points" in message


def test_schema_rejects_patient_identifier_fields():
    payload = CASES[0].model_dump(mode="python")
    payload["brief_presentation"] += " MRN: 123456"

    with pytest.raises(ValidationError, match="identifier"):
        VascularCase.model_validate(payload)


def test_category_filtering_returns_only_selected_category():
    for category in CATEGORIES:
        filtered = filter_cases(category)
        assert filtered
        assert all(case.category == category for case in filtered)


def test_random_selection_does_not_immediately_repeat():
    first = CASES[0]
    selected, _ = select_case(
        mode="Random vascular case",
        previous_case_id=first.case_id,
        rng=random.Random(7),
    )
    assert selected.case_id != first.case_id


def test_random_selection_uses_uncompleted_cases():
    remaining = CASES[-1]
    completed = [case.case_id for case in CASES[:-1]]
    selected, history = select_case(
        mode="Random vascular case",
        completed_case_ids=completed,
        rng=random.Random(2),
    )
    assert selected.case_id == remaining.case_id
    assert history == set(completed)


def test_history_resets_after_every_eligible_case_is_complete():
    all_ids = [case.case_id for case in CASES]
    selected, history = select_case(
        mode="Random vascular case",
        completed_case_ids=all_ids,
        previous_case_id=CASES[0].case_id,
        rng=random.Random(3),
    )
    assert history == set()
    assert selected.case_id != CASES[0].case_id


def test_category_selection_never_leaves_category():
    category = "Arterial emergencies"
    for seed in range(10):
        selected, _ = select_case(
            mode="Choose category",
            category=category,
            rng=random.Random(seed),
        )
        assert selected.category == category
