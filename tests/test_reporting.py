import json

from tests.test_scoring import expert_answers
from vascucase.case_data import CASE
from vascucase.reporting import build_report_json
from vascucase.scoring import score_case


def test_download_report_is_valid_json_and_an_independent_snapshot():
    answers = expert_answers()
    result = score_case(answers)
    feedback = {"mode": "test", "text": "Educational simulation only—not for patient care."}

    report_text = build_report_json(
        case_title=CASE["title"],
        learner_level="Surgical resident",
        answers=answers,
        result=result,
        feedback=feedback,
    )
    report = json.loads(report_text)

    assert report["schema_version"] == 1
    assert report["result"]["score"] == 100
    assert report["case"] == CASE["title"]
    assert report["safety"].startswith("Education only")

    answers["stage1"]["diagnosis"] = "changed after export"
    assert report["answers"]["stage1"]["diagnosis"] == "Acute lower-limb ischaemia"
