import pytest
from streamlit.testing.v1 import AppTest

from vascucase.cases import CASES_BY_ID


def _button(app, label):
    return next(item for item in app.button if item.label == label)


def _widget(items, label):
    return next(item for item in items if item.label == label)


def _visible_text(app):
    values = []
    for element_type in (
        "title",
        "header",
        "subheader",
        "caption",
        "markdown",
        "text",
        "info",
        "success",
        "warning",
        "error",
    ):
        for element in getattr(app, element_type):
            values.append(str(element.value))
    return "\n".join(values)


def _start_specific_case(case_id):
    app = AppTest.from_file("app.py").run(timeout=20)
    _widget(app.radio, "Case mode").set_value("Choose a specific case")
    app.run(timeout=20)
    _widget(app.selectbox, "Specific case").set_value(case_id)
    _button(app, "Start simulation").click().run(timeout=20)
    return app


def _complete_case(app, case_id):
    case = CASES_BY_ID[case_id]
    for index, stage in enumerate(case.stages, start=1):
        answer = next(
            option.option_id
            for option in stage.question.options
            if option.option_id in case.correct_actions
        )
        _widget(app.radio, stage.question.prompt).set_value(answer)
        label = "Submit case for scoring" if index == 4 else "Lock answer and continue"
        _button(app, label).click().run(timeout=20)
        assert not app.exception
    return app


@pytest.mark.parametrize(
    "case_id",
    ["ali_af_embolism_iib", "ruptured_infrarenal_aaa", "embolic_acute_mesenteric_ischaemia"],
)
def test_complete_three_distinct_case_flows_without_api_key(monkeypatch, case_id):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = _complete_case(_start_specific_case(case_id), case_id)

    assert app.session_state["stage"] == 5
    assert [(metric.label, metric.value) for metric in app.metric] == [
        ("Total score", "100/100"),
        ("Performance band", "Excellent"),
        ("Critical omissions", "0"),
    ]
    assert CASES_BY_ID[case_id].final_diagnosis in _visible_text(app)
    assert "Feedback source: Expert rubric-based feedback" in _visible_text(app)
    download = _widget(app.download_button, "Download performance report (JSON)")
    assert download.proto.ignore_rerun is True
    download.click().run(timeout=20)
    assert not app.exception


def test_diagnosis_is_concealed_until_case_submission(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    case = CASES_BY_ID["ruptured_infrarenal_aaa"]
    app = _start_specific_case(case.case_id)

    assert case.final_diagnosis not in _visible_text(app)
    for index, stage in enumerate(case.stages, start=1):
        answer = next(option.option_id for option in stage.question.options if option.option_id in case.correct_actions)
        _widget(app.radio, stage.question.prompt).set_value(answer)
        label = "Submit case for scoring" if index == 4 else "Lock answer and continue"
        _button(app, label).click().run(timeout=20)
        if index < 4:
            assert case.final_diagnosis not in _visible_text(app)

    assert case.final_diagnosis in _visible_text(app)


def test_required_answer_validation(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = _start_specific_case("symptomatic_carotid_tia")

    _button(app, "Lock answer and continue").click().run(timeout=20)

    assert app.session_state["stage"] == 1
    assert any("Select an answer" in error.value for error in app.error)


def test_restart_clears_answers_and_preserves_current_case(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    case = CASES_BY_ID["iliofemoral_dvt_phlegmasia"]
    app = _start_specific_case(case.case_id)
    first_stage = case.stages[0]
    correct = next(option.option_id for option in first_stage.question.options if option.option_id in case.correct_actions)
    _widget(app.radio, first_stage.question.prompt).set_value(correct)
    _button(app, "Lock answer and continue").click().run(timeout=20)

    _button(app, "Restart case").click().run(timeout=20)

    assert app.session_state["stage"] == 1
    assert app.session_state["selected_case_id"] == case.case_id
    assert app.session_state["answers"] == {}
    assert _widget(app.radio, first_stage.question.prompt).value is None
    assert any(button.label == "New vascular case" for button in app.button)


def test_new_case_workflow_preserves_history_and_returns_to_landing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    case_id = "penetrating_femoral_artery_trauma"
    app = _complete_case(_start_specific_case(case_id), case_id)

    _button(app, "New vascular case").click().run(timeout=20)

    assert app.session_state["stage"] == 0
    assert app.session_state["selected_case_id"] is None
    assert case_id in app.session_state["completed_case_ids"]
    assert app.session_state["previous_case_id"] == case_id
    assert any(button.label == "Start simulation" for button in app.button)


def test_incomplete_report_state_recovers_to_landing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = AppTest.from_file("app.py")
    app.session_state["stage"] = 5
    app.session_state["selected_case_id"] = "ali_af_embolism_iib"
    app.session_state["answers"] = {"stage1_decision": "ali_s1_urgent_bundle"}
    app.session_state["result"] = None
    app.session_state["feedback"] = None

    app.run(timeout=20)

    assert not app.exception
    assert app.session_state["stage"] == 0
    assert app.session_state["selected_case_id"] is None
    assert app.session_state["answers"] == {}
    assert any(button.label == "Start simulation" for button in app.button)
