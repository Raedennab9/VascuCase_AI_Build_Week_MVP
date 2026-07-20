import random

from vascucase.cases import CASES
from vascucase.presentation import build_option_orders, valid_option_orders


def _correct_position(case, stage, orders):
    correct_id = next(
        option.option_id
        for option in stage.question.options
        if option.option_id in case.correct_actions
    )
    return orders[stage.question.question_id].index(correct_id)


def test_correct_answer_can_appear_as_a_b_c_or_d():
    case = CASES[0]
    stage = case.stages[0]
    observed_positions = {
        _correct_position(
            case,
            stage,
            build_option_orders(case, rng=random.Random(seed)),
        )
        for seed in range(100)
    }

    assert observed_positions == {0, 1, 2, 3}


def test_repeat_attempt_moves_every_single_correct_answer():
    case = CASES[0]
    first = build_option_orders(case, rng=random.Random(11))
    restarted = build_option_orders(
        case,
        previous_orders=first,
        rng=random.Random(11),
    )

    assert valid_option_orders(case, first)
    assert valid_option_orders(case, restarted)
    for stage in case.stages:
        assert _correct_position(case, stage, restarted) != _correct_position(case, stage, first)


def test_every_case_order_is_a_complete_option_permutation():
    for case in CASES:
        assert valid_option_orders(case, build_option_orders(case, rng=random.Random(5)))
