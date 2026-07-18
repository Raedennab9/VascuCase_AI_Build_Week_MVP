from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from vascucase.cases.schema import VascularCase


def _selected_ids(answers: dict[str, Any]) -> set[str]:
    selected: set[str] = set()
    for value in answers.values():
        if isinstance(value, str):
            selected.add(value)
        elif isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
            selected.update(item for item in value if isinstance(item, str))
    return selected


def performance_band(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Developing"
    return "Needs improvement"


def score_case(case: VascularCase, answers: dict[str, Any]) -> dict[str, Any]:
    """Apply the case rubric without any model-generated judgment."""
    selected = _selected_ids(answers)
    labels = case.option_labels
    domains = case.option_domains

    correct_ids = [option_id for option_id in case.correct_actions if option_id in selected]
    missed_correct_ids = [option_id for option_id in case.correct_actions if option_id not in selected]
    missed_critical_ids = [option_id for option_id in case.critical_actions if option_id not in selected]
    unsafe_ids = [option_id for option_id in case.unsafe_choices if option_id in selected]

    domain_max = case.domain_max_scores
    domain_raw = {domain: 0 for domain in domain_max}
    domain_penalties = {domain: 0 for domain in domain_max}
    for option_id in correct_ids:
        domain_raw[domains[option_id]] += case.scoring_weights[option_id]
    for option_id in unsafe_ids:
        domain_penalties[domains[option_id]] += case.unsafe_choices[option_id].penalty

    domain_scores = {
        domain: {
            "score": max(0, domain_raw[domain] - domain_penalties[domain]),
            "max_score": maximum,
            "unsafe_penalty": domain_penalties[domain],
        }
        for domain, maximum in domain_max.items()
    }
    score = sum(item["score"] for item in domain_scores.values())

    correct_actions = [labels[option_id] for option_id in correct_ids]
    critical_omissions = [labels[option_id] for option_id in missed_critical_ids]
    unsafe_selections = [
        {
            "action": labels[option_id],
            "explanation": case.unsafe_choices[option_id].explanation,
            "penalty": case.unsafe_choices[option_id].penalty,
        }
        for option_id in unsafe_ids
    ]
    improvements = [
        case.explanations[option_id]
        for option_id in missed_correct_ids
    ] + [item["explanation"] for item in unsafe_selections]

    return {
        "score": score,
        "max_score": 100,
        "band": performance_band(score),
        "domain_scores": domain_scores,
        "correct_actions": correct_actions,
        "critical_omissions": critical_omissions,
        "unsafe_selections": unsafe_selections,
        "strengths": [case.explanations[option_id] for option_id in correct_ids],
        "improvements": list(dict.fromkeys(improvements)),
        "selected_option_ids": sorted(selected & set(labels)),
    }
