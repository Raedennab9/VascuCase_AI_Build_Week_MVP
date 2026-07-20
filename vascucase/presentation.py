from __future__ import annotations

import random
from collections.abc import Mapping, Sequence

from vascucase.cases.schema import VascularCase


OptionOrders = dict[str, list[str]]


def valid_option_orders(case: VascularCase, orders: object) -> bool:
    if not isinstance(orders, Mapping):
        return False
    for stage in case.stages:
        question = stage.question
        declared = [option.option_id for option in question.options]
        ordered = orders.get(question.question_id)
        if not isinstance(ordered, Sequence) or isinstance(ordered, (str, bytes)):
            return False
        if len(ordered) != len(declared) or set(ordered) != set(declared):
            return False
    return True


def build_option_orders(
    case: VascularCase,
    *,
    previous_orders: Mapping[str, Sequence[str]] | None = None,
    rng: random.Random | random.SystemRandom | None = None,
) -> OptionOrders:
    """Shuffle choices while moving each single correct answer on a repeat attempt."""
    randomizer = rng or random.SystemRandom()
    orders: OptionOrders = {}

    for stage in case.stages:
        question = stage.question
        option_ids = [option.option_id for option in question.options]
        randomizer.shuffle(option_ids)

        correct_ids = set(option_ids) & set(case.correct_actions)
        previous = previous_orders.get(question.question_id) if previous_orders else None
        previous_is_valid = (
            isinstance(previous, Sequence)
            and not isinstance(previous, (str, bytes))
            and len(previous) == len(option_ids)
            and set(previous) == set(option_ids)
        )

        if question.kind == "single" and len(correct_ids) == 1 and previous_is_valid:
            correct_id = next(iter(correct_ids))
            previous_position = list(previous).index(correct_id)
            current_position = option_ids.index(correct_id)
            if current_position == previous_position:
                replacement_positions = [
                    index for index in range(len(option_ids)) if index != previous_position
                ]
                replacement_position = randomizer.choice(replacement_positions)
                option_ids[current_position], option_ids[replacement_position] = (
                    option_ids[replacement_position],
                    option_ids[current_position],
                )

        orders[question.question_id] = option_ids

    return orders
