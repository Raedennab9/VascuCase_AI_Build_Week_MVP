from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from vascucase.cases.schema import VascularCase


def build_report(
    *,
    case: VascularCase,
    learner_level: str,
    result: dict[str, Any],
    feedback_source: str,
    completion_timestamp: str | None = None,
) -> dict[str, Any]:
    """Create an identifier-free report from rubric-controlled fields only."""
    completed_at = completion_timestamp or datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": 2,
        "project": "VascuCase AI",
        "case_id": case.case_id,
        "case_title": case.title,
        "category": case.category,
        "learner_level": learner_level,
        "total_score": result["score"],
        "maximum_score": result["max_score"],
        "performance_band": result["band"],
        "domain_scores": deepcopy(result["domain_scores"]),
        "correct_actions": deepcopy(result["correct_actions"]),
        "critical_omissions": deepcopy(result["critical_omissions"]),
        "unsafe_selections": deepcopy(result["unsafe_selections"]),
        "completion_timestamp": completed_at,
        "feedback_source": feedback_source,
        "safety": "Education only; fictional simulation; not for patient care.",
    }


def build_report_json(**kwargs: Any) -> str:
    return json.dumps(build_report(**kwargs), indent=2, ensure_ascii=False)
