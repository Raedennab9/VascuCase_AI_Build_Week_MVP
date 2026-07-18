from copy import deepcopy
from types import SimpleNamespace

import openai

from tests.test_scoring import expert_answers
from vascucase.case_data import CASE
from vascucase.feedback import generate_feedback
from vascucase.scoring import score_case


def test_model_request_excludes_free_text_and_preserves_authoritative_data(monkeypatch):
    answers = expert_answers()
    answers["stage1"]["reasoning"] = "PRIVATE FREE TEXT"
    answers["stage2"]["rationale"] = "PRIVATE RATIONALE"
    answers["stage4"]["plan"] = "PRIVATE PLAN"
    result = score_case(answers)
    original_result = deepcopy(result)
    original_pathway = deepcopy(CASE["model_pathway"])
    captured = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                output_text="Strong recognition. Keep prioritizing urgent reperfusion. "
                "Educational simulation only—not for patient care."
            )

    class FakeClient:
        responses = FakeResponses()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.6")
    monkeypatch.setattr(openai, "OpenAI", lambda **kwargs: FakeClient())

    feedback = generate_feedback(
        case=CASE,
        answers=answers,
        result=result,
        learner_level="Surgical resident",
        safety_identifier="anonymous-session",
    )

    assert "PRIVATE" not in captured["input"]
    assert captured["model"] == "gpt-5.6"
    assert captured["reasoning"] == {"effort": "low"}
    assert captured["text"] == {"verbosity": "low"}
    assert captured["store"] is False
    assert captured["safety_identifier"] == "anonymous-session"
    assert result == original_result
    assert CASE["model_pathway"] == original_pathway
    assert "deterministic score unchanged" in feedback["mode"]


def test_feedback_uses_deterministic_fallback_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    answers = expert_answers()
    result = score_case(answers)

    feedback = generate_feedback(
        case=CASE,
        answers=answers,
        result=result,
        learner_level="Medical student",
    )

    assert "fallback" in feedback["mode"].lower()
    assert "100/100" in feedback["text"]
