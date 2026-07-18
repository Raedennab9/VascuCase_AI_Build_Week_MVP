from copy import deepcopy
from types import SimpleNamespace

import openai

from tests.test_scoring import expert_answers
from vascucase.cases import CASES
from vascucase.feedback import AI_SOURCE, EXPERT_SOURCE, generate_feedback
from vascucase.scoring import score_case


def test_feedback_uses_case_specific_offline_path_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    case = CASES[1]
    result = score_case(case, expert_answers(case))

    feedback = generate_feedback(case=case, result=result, learner_level="Medical student")

    assert feedback["source"] == EXPERT_SOURCE
    assert "100/100" in feedback["text"]
    assert case.learning_points[0] in feedback["text"]


def test_valid_model_response_is_explanation_only_and_preserves_authoritative_data(monkeypatch):
    case = CASES[0]
    result = score_case(case, expert_answers(case))
    original_result = deepcopy(result)
    original_case = case.model_dump(mode="json")
    captured = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output_text="AI coaching. Educational simulation only—not for patient care.")

    class FakeClient:
        responses = FakeResponses()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.6")
    monkeypatch.setattr(openai, "OpenAI", lambda **kwargs: FakeClient())

    feedback = generate_feedback(
        case=case,
        result=result,
        learner_level="Surgical resident",
        safety_identifier="anonymous-session",
    )

    assert feedback["source"] == AI_SOURCE
    assert captured["model"] == "gpt-5.6"
    assert captured["reasoning"] == {"effort": "low"}
    assert captured["text"] == {"verbosity": "low"}
    assert captured["store"] is False
    assert captured["safety_identifier"] == "anonymous-session"
    assert result == original_result
    assert case.model_dump(mode="json") == original_case


def test_api_error_is_never_labeled_ai_enhanced(monkeypatch):
    case = CASES[0]
    result = score_case(case, expert_answers(case))

    class BrokenClient:
        class responses:
            @staticmethod
            def create(**kwargs):
                raise RuntimeError("offline")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(openai, "OpenAI", lambda **kwargs: BrokenClient())

    feedback = generate_feedback(case=case, result=result, learner_level="Vascular trainee")

    assert feedback["source"] == EXPERT_SOURCE
