import pytest

from vascucase.case_data import CASE
from vascucase.scoring import score_case


def expert_answers():
    return {
        "stage1": {
            "diagnosis": "Acute lower-limb ischaemia",
            "priorities": [
                "Urgently activate the vascular team",
                "Start intravenous unfractionated heparin unless contraindicated",
                "Provide analgesia and establish intravenous access",
                "Keep the patient fasting and obtain urgent baseline blood tests/crossmatch",
            ],
            "reasoning": "Abrupt ischaemic symptoms with neurological deficit.",
        },
        "stage2": {
            "classification": "Rutherford IIb — immediately threatened",
            "decisive": [
                "Sensory loss extending beyond the toes",
                "Mild motor weakness",
                "Absent distal arterial Doppler signal with preserved venous signal",
            ],
            "rationale": "Motor weakness and sensory loss beyond toes.",
        },
        "stage3": {
            "investigation": "Immediate anatomical imaging only if it does not delay urgent revascularization",
            "adjuncts": [
                "Bedside continuous-wave Doppler assessment",
                "Full blood count, coagulation profile, electrolytes, creatinine and creatine kinase",
                "ECG and later embolic-source evaluation",
                "Group and crossmatch blood",
            ],
        },
        "stage4": {
            "urgency": "Immediate/urgent revascularization",
            "strategies": [
                "Urgent surgical embolectomy/thrombectomy when anatomy and expertise favour it",
                "Urgent endovascular or hybrid thrombus-removal strategy when appropriate and immediately available",
                "Treat any underlying arterial lesion identified after thrombus removal",
                "Monitor for reperfusion injury and compartment syndrome; consider fasciotomy when indicated",
                "Investigate the embolic source and plan long-term stroke/systemic embolism prevention",
            ],
            "plan": "Urgent reperfusion with post-reperfusion monitoring.",
        },
    }


def test_expert_path_scores_100():
    result = score_case(expert_answers())
    assert result["score"] == 100
    assert result["band"] == "Excellent"
    assert result["critical_misses"] == []


def test_dangerous_delay_is_flagged():
    answers = expert_answers()
    answers["stage3"]["investigation"] = "Routine CTA first, even if revascularization is delayed"
    result = score_case(answers)
    assert any("must not delay" in item for item in result["critical_misses"])
    assert result["score"] < 100


def test_wrong_classification_is_flagged():
    answers = expert_answers()
    answers["stage2"]["classification"] = "Rutherford IIa — marginally threatened"
    result = score_case(answers)
    assert any("Rutherford IIb" in item for item in result["critical_misses"])
    assert result["score"] <= 85


def test_systemic_thrombolysis_is_penalized():
    answers = expert_answers()
    answers["stage4"]["strategies"].append("Use systemic intravenous thrombolysis as routine therapy")
    result = score_case(answers)
    assert any("Systemic intravenous thrombolysis" in item for item in result["critical_misses"])
    assert result["score"] < 100


def test_compression_and_outpatient_delay_are_penalized():
    answers = expert_answers()
    answers["stage1"]["priorities"].extend([
        "Apply compression and elevate the limb",
        "Wait for routine outpatient vascular imaging",
    ])
    result = score_case(answers)
    assert any("outpatient" in item.lower() for item in result["critical_misses"])
    assert any("compression" in item.lower() for item in result["improvements"])
    assert result["score"] < 100


def test_exercise_abi_is_penalized():
    answers = expert_answers()
    answers["stage3"]["adjuncts"].append("Exercise ankle–brachial pressure testing")
    result = score_case(answers)
    assert any("Exercise ABI" in item for item in result["improvements"])
    assert result["score"] < 100


def test_waiting_for_motor_recovery_is_dangerous():
    answers = expert_answers()
    answers["stage4"]["strategies"].append("Delay intervention until motor weakness resolves")
    result = score_case(answers)
    assert any("Motor weakness increases urgency" in item for item in result["critical_misses"])
    assert result["score"] < 100


@pytest.mark.parametrize(
    ("stage", "field", "option", "message_group", "message_fragment"),
    [
        (
            "stage1",
            "priorities",
            "Apply compression and elevate the limb",
            "improvements",
            "compression",
        ),
        (
            "stage1",
            "priorities",
            "Wait for routine outpatient vascular imaging",
            "critical_misses",
            "outpatient",
        ),
        (
            "stage3",
            "investigation",
            "Routine CTA first, even if revascularization is delayed",
            "critical_misses",
            "must not delay",
        ),
        (
            "stage3",
            "adjuncts",
            "Exercise ankle–brachial pressure testing",
            "improvements",
            "Exercise ABI",
        ),
        (
            "stage4",
            "strategies",
            "Use systemic intravenous thrombolysis as routine therapy",
            "critical_misses",
            "Systemic intravenous thrombolysis",
        ),
        (
            "stage4",
            "strategies",
            "Delay intervention until motor weakness resolves",
            "critical_misses",
            "Motor weakness increases urgency",
        ),
    ],
    ids=[
        "compression",
        "outpatient-delay",
        "delayed-cta",
        "exercise-abi",
        "systemic-thrombolysis",
        "wait-for-motor-recovery",
    ],
)
def test_every_explicitly_penalized_unsafe_option_is_flagged(
    stage, field, option, message_group, message_fragment
):
    answers = expert_answers()
    if isinstance(answers[stage][field], list):
        answers[stage][field].append(option)
    else:
        answers[stage][field] = option

    result = score_case(answers)

    assert result["score"] < 100
    assert any(message_fragment in message for message in result[message_group])


SINGLE_SELECT_EXPERT_INDEX = {
    ("stage1", "diagnosis_options"): 0,
    ("stage2", "classification_options"): 2,
    ("stage3", "investigation_options"): 0,
    ("stage4", "urgency_options"): 0,
}


@pytest.mark.parametrize(
    ("stage", "field", "option"),
    [
        (stage, option_key.removesuffix("_options"), option)
        for (stage, option_key), expert_index in SINGLE_SELECT_EXPERT_INDEX.items()
        for index, option in enumerate(CASE[stage][option_key])
        if index != expert_index
    ],
)
def test_every_non_expert_single_choice_is_flagged(stage, field, option):
    answers = expert_answers()
    answers[stage][field] = option

    result = score_case(answers)

    assert result["score"] < 100
    assert result["critical_misses"] or result["improvements"]
