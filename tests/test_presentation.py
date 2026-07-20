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


def test_every_case_stage_correct_answer_can_appear_as_a_b_c_or_d():
    for case in CASES:
        seeded_orders = [
            build_option_orders(case, rng=random.Random(seed))
            for seed in range(100)
        ]
        for stage in case.stages:
            observed_positions = {
                _correct_position(case, stage, orders)
                for orders in seeded_orders
            }
            assert observed_positions == {0, 1, 2, 3}, (
                case.case_id,
                stage.stage_id,
                observed_positions,
            )


def test_repeat_attempt_moves_every_single_correct_answer_in_every_case():
    for case in CASES:
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
