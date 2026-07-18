import json

from tests.test_scoring import expert_answers
from vascucase.cases import CASES
from vascucase.feedback import EXPERT_SOURCE
from vascucase.reporting import build_report_json
from vascucase.scoring import score_case


def test_report_contains_case_metadata_and_no_unrestricted_answers():
    case = CASES[3]
    result = score_case(case, expert_answers(case))
    timestamp = "2026-07-19T00:00:00+00:00"

    report = json.loads(
        build_report_json(
            case=case,
            learner_level="Surgical resident",
            result=result,
            feedback_source=EXPERT_SOURCE,
            completion_timestamp=timestamp,
        )
    )

    assert report["schema_version"] == 2
    assert report["case_id"] == case.case_id
    assert report["case_title"] == case.title
    assert report["category"] == case.category
    assert report["total_score"] == 100
    assert report["performance_band"] == "Excellent"
    assert report["completion_timestamp"] == timestamp
    assert report["feedback_source"] == EXPERT_SOURCE
    assert "answers" not in report
    assert "feedback_text" not in report
    assert set(report) >= {
        "domain_scores",
        "correct_actions",
        "critical_omissions",
        "unsafe_selections",
    }
