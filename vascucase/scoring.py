from __future__ import annotations

from typing import Any


def _selected(answers: dict[str, Any], stage: str, field: str) -> set[str]:
    value = answers.get(stage, {}).get(field, [])
    if value is None:
        return set()
    if isinstance(value, str):
        return {value}
    return set(value)


def score_case(answers: dict[str, Any]) -> dict[str, Any]:
    sections: dict[str, dict[str, Any]] = {}
    strengths: list[str] = []
    critical_misses: list[str] = []
    improvements: list[str] = []

    # 1. Recognition and first actions — 30 points
    s1 = answers.get("stage1", {})
    priorities = _selected(answers, "stage1", "priorities")
    recognition = 0
    notes: list[str] = []
    if s1.get("diagnosis") == "Acute lower-limb ischaemia":
        recognition += 10
        strengths.append("Correctly recognized acute lower-limb ischaemia.")
    else:
        critical_misses.append("Recognize the presentation as acute limb ischaemia.")
    if "Urgently activate the vascular team" in priorities:
        recognition += 7
        strengths.append("Escalated promptly to the vascular team.")
    else:
        critical_misses.append("Urgently activate a vascular specialist/team.")
    if "Start intravenous unfractionated heparin unless contraindicated" in priorities:
        recognition += 8
        strengths.append("Selected immediate unfractionated heparin in the absence of a contraindication.")
    else:
        critical_misses.append("Start intravenous unfractionated heparin promptly unless contraindicated.")
    if "Provide analgesia and establish intravenous access" in priorities:
        recognition += 3
    if "Keep the patient fasting and obtain urgent baseline blood tests/crossmatch" in priorities:
        recognition += 2
    if "Apply compression and elevate the limb" in priorities:
        recognition -= 5
        improvements.append("Avoid compression/elevation as a treatment for acute arterial ischaemia.")
    if "Wait for routine outpatient vascular imaging" in priorities:
        recognition -= 8
        critical_misses.append("Do not defer a threatened limb to outpatient assessment.")
    recognition = max(0, min(recognition, 30))
    notes.append("Immediate recognition, anticoagulation, analgesia, preparation, and vascular escalation are assessed.")
    sections["Recognition and first actions"] = {"score": recognition, "max_score": 30, "note": " ".join(notes)}

    # 2. Rutherford classification — 25 points
    s2 = answers.get("stage2", {})
    decisive = _selected(answers, "stage2", "decisive")
    classification = 0
    if s2.get("classification") == "Rutherford IIb — immediately threatened":
        classification += 15
        strengths.append("Correctly classified the limb as Rutherford IIb.")
    else:
        critical_misses.append("Classify sensory loss beyond the toes with motor weakness as Rutherford IIb.")
    for finding in [
        "Sensory loss extending beyond the toes",
        "Mild motor weakness",
        "Absent distal arterial Doppler signal with preserved venous signal",
    ]:
        if finding in decisive:
            classification += 3
    if all(
        finding in decisive
        for finding in ["Sensory loss extending beyond the toes", "Mild motor weakness"]
    ):
        classification += 1
    if classification < 22:
        improvements.append("Give neurological findings—especially motor deficit—the greatest weight when determining urgency.")
    classification = min(classification, 25)
    sections["Limb viability classification"] = {
        "score": classification,
        "max_score": 25,
        "note": "Rutherford IIb is defined here by sensory loss beyond the toes and mild motor weakness, with absent arterial Doppler signals.",
    }

    # 3. Investigation strategy — 15 points
    s3 = answers.get("stage3", {})
    adjuncts = _selected(answers, "stage3", "adjuncts")
    investigation = 0
    if s3.get("investigation") == "Immediate anatomical imaging only if it does not delay urgent revascularization":
        investigation += 9
        strengths.append("Prioritized rapid anatomical definition without delaying reperfusion.")
    elif s3.get("investigation") == "Routine CTA first, even if revascularization is delayed":
        critical_misses.append("Imaging must not delay revascularization in a limb with neurological deficit.")
    else:
        improvements.append("Use immediate, treatment-directed imaging while protecting time to reperfusion.")
    for item, pts in {
        "Bedside continuous-wave Doppler assessment": 1,
        "Full blood count, coagulation profile, electrolytes, creatinine and creatine kinase": 2,
        "ECG and later embolic-source evaluation": 1,
        "Group and crossmatch blood": 2,
    }.items():
        if item in adjuncts:
            investigation += pts
    if "Exercise ankle–brachial pressure testing" in adjuncts:
        investigation -= 2
        improvements.append("Exercise ABI testing is inappropriate in this time-critical acute presentation.")
    investigation = max(0, min(investigation, 15))
    sections["Investigation strategy"] = {
        "score": investigation,
        "max_score": 15,
        "note": "Parallel tests are useful only when they do not postpone reperfusion.",
    }

    # 4. Revascularization and surveillance — 30 points
    s4 = answers.get("stage4", {})
    strategies = _selected(answers, "stage4", "strategies")
    management = 0
    if s4.get("urgency") == "Immediate/urgent revascularization":
        management += 10
        strengths.append("Selected immediate revascularization for an immediately threatened limb.")
    else:
        critical_misses.append("Rutherford IIb acute limb ischaemia requires immediate/urgent revascularization.")
    scored_strategies = {
        "Urgent surgical embolectomy/thrombectomy when anatomy and expertise favour it": 5,
        "Urgent endovascular or hybrid thrombus-removal strategy when appropriate and immediately available": 4,
        "Treat any underlying arterial lesion identified after thrombus removal": 3,
        "Monitor for reperfusion injury and compartment syndrome; consider fasciotomy when indicated": 4,
        "Investigate the embolic source and plan long-term stroke/systemic embolism prevention": 4,
    }
    for item, pts in scored_strategies.items():
        if item in strategies:
            management += pts
    if (
        "Urgent surgical embolectomy/thrombectomy when anatomy and expertise favour it" in strategies
        or "Urgent endovascular or hybrid thrombus-removal strategy when appropriate and immediately available" in strategies
    ):
        strengths.append("Chose a time-efficient open/endovascular/hybrid reperfusion pathway based on anatomy and expertise.")
    else:
        critical_misses.append("Select an urgent open, endovascular, or hybrid reperfusion strategy.")
    if "Use systemic intravenous thrombolysis as routine therapy" in strategies:
        management -= 6
        critical_misses.append("Systemic intravenous thrombolysis is not routine treatment for acute limb ischaemia.")
    if "Delay intervention until motor weakness resolves" in strategies:
        management -= 8
        critical_misses.append("Motor weakness increases urgency; it is not a reason to wait.")
    management = max(0, min(management, 30))
    if "Monitor for reperfusion injury and compartment syndrome; consider fasciotomy when indicated" not in strategies:
        improvements.append("Add post-reperfusion surveillance for compartment syndrome and metabolic complications.")
    sections["Revascularization and surveillance"] = {
        "score": management,
        "max_score": 30,
        "note": "The rubric accepts the fastest appropriate open, endovascular, or hybrid strategy rather than prescribing one universal procedure.",
    }

    score = sum(section["score"] for section in sections.values())
    if score >= 85 and not critical_misses:
        band = "Excellent"
    elif score >= 70:
        band = "Competent"
    elif score >= 50:
        band = "Developing"
    else:
        band = "Needs focused review"

    # Keep the report concise and deduplicated.
    strengths = list(dict.fromkeys(strengths))
    critical_misses = list(dict.fromkeys(critical_misses))
    improvements = list(dict.fromkeys(improvements))

    return {
        "score": score,
        "max_score": 100,
        "band": band,
        "sections": sections,
        "strengths": strengths,
        "critical_misses": critical_misses,
        "improvements": improvements,
    }
