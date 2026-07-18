from __future__ import annotations

import json
import os
from typing import Any


def _fallback_feedback(result: dict[str, Any], learner_level: str) -> str:
    strengths = result.get("strengths", [])
    misses = result.get("critical_misses", [])
    improvements = result.get("improvements", [])

    parts = [
        f"At the {learner_level.lower()} level, your performance was graded **{result['band']}** "
        f"with a score of **{result['score']}/100**."
    ]
    if strengths:
        parts.append("You performed well in: " + "; ".join(strengths[:3]))
    if misses:
        parts.append("The highest-priority correction is: " + "; ".join(misses[:3]))
    if improvements:
        parts.append("For the next attempt, focus on: " + "; ".join(improvements[:3]))
    parts.append(
        "The central learning point is that neurological deficit in acute limb ischaemia makes the limb immediately threatened: "
        "anticoagulate unless contraindicated, involve the vascular team, and proceed to urgent revascularization without harmful imaging delay."
    )
    return "\n\n".join(parts)


def generate_feedback(
    *,
    case: dict[str, Any],
    answers: dict[str, Any],
    result: dict[str, Any],
    learner_level: str,
) -> dict[str, str]:
    """Generate feedback with GPT-5.6 when configured; otherwise use a deterministic fallback."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"mode": "Rubric-based fallback (no API key configured)", "text": _fallback_feedback(result, learner_level)}

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-5.6")
        payload = {
            "learner_level": learner_level,
            "fictional_case": case["title"],
            "answers": answers,
            "validated_scoring_result": result,
            "model_pathway": case["model_pathway"],
        }
        instructions = (
            "You are an expert vascular-surgery educator. Produce concise formative feedback for a fictional educational case. "
            "Treat the supplied deterministic scoring result and model pathway as authoritative. Do not change the score, invent new "
            "clinical facts, provide patient-specific advice, or imply that the tool is suitable for real clinical care. Explain the most "
            "important strength, the most dangerous omission, and one concrete improvement. Adapt vocabulary to the learner level. "
            "Use 180-260 words and end with: 'Educational simulation only—not for patient care.'"
        )
        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=json.dumps(payload, ensure_ascii=False),
            max_output_tokens=500,
        )
        text = (response.output_text or "").strip()
        if not text:
            raise RuntimeError("The model returned no text.")
        return {"mode": f"GPT-5.6 personalized feedback ({model})", "text": text}
    except Exception as exc:  # The app must remain testable without API/model access.
        return {
            "mode": f"Rubric fallback after API error: {type(exc).__name__}",
            "text": _fallback_feedback(result, learner_level),
        }
