from __future__ import annotations

import json
from copy import deepcopy
from typing import Any


def build_report(
    *,
    case_title: str,
    learner_level: str,
    answers: dict[str, Any],
    result: dict[str, Any],
    feedback: dict[str, str],
) -> dict[str, Any]:
    """Create a portable snapshot of a fictional simulation attempt."""
    return {
        "schema_version": 1,
        "project": "VascuCase AI",
        "case": case_title,
        "learner_level": learner_level,
        "answers": deepcopy(answers),
        "result": deepcopy(result),
        "feedback": deepcopy(feedback),
        "safety": "Education only; fictional simulation; not for patient care.",
    }


def build_report_json(**kwargs: Any) -> str:
    """Serialize a report as readable UTF-8 JSON without mutating source state."""
    return json.dumps(build_report(**kwargs), indent=2, ensure_ascii=False)
