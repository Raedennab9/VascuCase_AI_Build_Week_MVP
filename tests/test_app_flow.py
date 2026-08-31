import logging
from uuid import UUID, uuid4

import pytest
from streamlit.testing.v1 import AppTest

from vascucase import database
from vascucase.cases import CASES_BY_ID
from tests.fake_database import FakeDatabase


@pytest.fixture(autouse=True)
def fake_database(monkeypatch):
    fake = FakeDatabase()
    fake.install(monkeypatch)
    yield fake


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


def _fill_registration(
    app,
    *,
    full_name="Alex Morgan",
    email="alex@example.com",
    learner_level="Surgical resident",
    institution="Yarmouk University",
    institution_number="",
):
    _widget(app.text_input, "Full name *").set_value(full_name)
    _widget(app.text_input, "Email address *").set_value(email)
    _widget(app.selectbox, "Current training level *").set_value(learner_level)
    _widget(app.text_input, "Institution / University *").set_value(institution)
    if institution_number:
        _widget(
            app.text_input,
            "University / Institutional Number (required for Medical students)",
        ).set_value(institution_number)
    privacy_checkbox = next(
        item for item in app.checkbox if item.label.startswith("I consent")
    )
    privacy_checkbox.set_value(True)
    return app


def _register(app, **kwargs):
    _fill_registration(app, **kwargs)
    _button(app, "Register and continue").click().run(timeout=20)
    assert not app.exception
    return app


def _start_specific_case(case_id):
    app = AppTest.from_file("app.py").run(timeout=20)
    _register(app)
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


def test_registration_gate_hides_case_library(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)

    assert not app.exception
    assert app.session_state["registration_complete"] is False
    assert app.session_state["participant_id"] is None
    assert app.session_state["registration_receipt"] is None
    assert any(item.label == "Register and continue" for item in app.button)
    assert not any(button.label == "Start simulation" for button in app.button)
    assert not any(radio.label == "Case mode" for radio in app.radio)


def test_registration_validates_all_missing_fields(monkeypatch, fake_database):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)
    next(item for item in app.checkbox if item.label.startswith("I consent")).set_value(True)

    _button(app, "Register and continue").click().run(timeout=20)

    errors = [item.value for item in app.error]
    assert "Enter a full name between 2 and 120 characters." in errors
    assert "Enter a valid email address." in errors
    assert "Select your current training level." in errors
    assert "Enter your institution." in errors
    assert app.session_state["registration_complete"] is False
    assert fake_database.registration_calls == []


@pytest.mark.parametrize(
    ("missing_field", "expected_error"),
    [
        ("name", "Enter a full name between 2 and 120 characters."),
        ("email", "Enter a valid email address."),
        ("level", "Select your current training level."),
        ("institution", "Enter your institution."),
    ],
)
def test_each_missing_registration_field_is_rejected(
    monkeypatch, fake_database, missing_field, expected_error
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)
    _widget(app.text_input, "Full name *").set_value(
        " " if missing_field == "name" else "Alex Morgan"
    )
    _widget(app.text_input, "Email address *").set_value(
        "" if missing_field == "email" else "alex@example.com"
    )
    if missing_field != "level":
        _widget(app.selectbox, "Current training level *").set_value(
            "Surgical resident"
        )
    _widget(app.text_input, "Institution / University *").set_value(
        " " if missing_field == "institution" else "Yarmouk University"
    )
    next(item for item in app.checkbox if item.label.startswith("I consent")).set_value(True)

    _button(app, "Register and continue").click().run(timeout=20)

    assert expected_error in [item.value for item in app.error]
    assert app.session_state["registration_complete"] is False
    assert fake_database.registration_calls == []


def test_registration_rejects_invalid_email(monkeypatch, fake_database):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)
    _fill_registration(app, email="not-an-email")

    _button(app, "Register and continue").click().run(timeout=20)

    assert "Enter a valid email address." in [item.value for item in app.error]
    assert app.session_state["registration_complete"] is False
    assert fake_database.registration_calls == []


def test_registration_requires_consent(monkeypatch, fake_database):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)
    _widget(app.text_input, "Full name *").set_value("Alex Morgan")
    _widget(app.text_input, "Email address *").set_value("alex@example.com")
    _widget(app.selectbox, "Current training level *").set_value(
        "Surgical resident"
    )
    _widget(app.text_input, "Institution / University *").set_value(
        "Yarmouk University"
    )

    _button(app, "Register and continue").click().run(timeout=20)

    assert "Read and accept the privacy and data-use notice to continue." in [
        item.value for item in app.error
    ]
    assert app.session_state["registration_complete"] is False
    assert fake_database.registration_calls == []


def test_medical_student_requires_institution_number_in_ui(
    monkeypatch, fake_database
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)
    _fill_registration(app, learner_level="Medical student")

    _button(app, "Register and continue").click().run(timeout=20)

    assert "Institution number is required for medical students." in [
        item.value for item in app.error
    ]
    assert app.session_state["registration_complete"] is False
    assert fake_database.registration_calls == []


def test_medical_student_institution_number_preserves_leading_zeroes(
    monkeypatch, fake_database
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = _register(
        AppTest.from_file("app.py").run(timeout=20),
        learner_level="Medical student",
        institution="  Yarmouk    University ",
        institution_number="  00127-A  ",
    )

    assert app.session_state["registration_complete"] is True
    assert app.session_state["registration_profile"]["institution"] == (
        "Yarmouk University"
    )
    assert app.session_state["registration_profile"]["institution_number"] == (
        "00127-A"
    )
    assert fake_database.registration_calls[0]["institution_number"] == "00127-A"


def test_training_level_widget_uses_the_database_contract(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)
    widget = _widget(app.selectbox, "Current training level *")

    assert tuple(
        option
        for option in widget.options
        if option in database.TRAINING_LEVELS
    ) == tuple(database.TRAINING_LEVELS)


def test_successful_registration_normalizes_and_stores_only_submitted_profile(
    monkeypatch, fake_database
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = _register(
        AppTest.from_file("app.py").run(timeout=20),
        full_name="  Alex   Morgan  ",
        email="  ALEX@Example.COM ",
        learner_level="Vascular trainee",
        institution="  Yarmouk    University ",
    )

    profile = app.session_state["registration_profile"]
    participant_id = app.session_state["participant_id"]
    receipt = app.session_state["registration_receipt"]
    assert app.session_state["registration_complete"] is True
    assert str(UUID(participant_id)) == participant_id
    assert isinstance(receipt, str) and len(receipt) == 64
    assert int(receipt, 16) >= 0
    assert app.session_state["learner_level"] == "Vascular trainee"
    assert profile == {
        "participant_id": participant_id,
        "name": "Alex Morgan",
        "email": "alex@example.com",
        "training_level": "Vascular trainee",
        "institution": "Yarmouk University",
        "institution_number": None,
        "consent_given": True,
        "consent_version": database.CONSENT_VERSION,
    }
    assert len(fake_database.participants_by_email) == 1
    assert fake_database.registration_calls == [
        {
            "name": "Alex Morgan",
            "email": "alex@example.com",
            "training_level": "Vascular trainee",
            "institution": "Yarmouk University",
            "institution_number": None,
            "consent_given": True,
            "consent_version": database.CONSENT_VERSION,
        }
    ]
    visible = _visible_text(app)
    stored = fake_database.participants_by_email["alex@example.com"]
    assert participant_id not in visible
    assert participant_id[-8:].upper() not in visible
    assert stored.registered_at.isoformat() not in visible
    assert stored.consented_at.isoformat() not in visible
    assert any(button.label == "Start simulation" for button in app.button)
    assert not any(button.label == "Register and continue" for button in app.button)

    app.run(timeout=20)
    assert app.session_state["participant_id"] == participant_id
    assert app.session_state["learner_level"] == "Vascular trainee"
    assert app.session_state["registration_profile"] == profile


def test_duplicate_exact_registration_reuses_id_without_exposing_history(
    monkeypatch, fake_database
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    first = _register(
        AppTest.from_file("app.py").run(timeout=20),
        email="Alex@Example.com",
    )
    first_id = first.session_state["participant_id"]
    original = fake_database.participants_by_email["alex@example.com"]

    second = _register(
        AppTest.from_file("app.py").run(timeout=20),
        email="  alex@example.COM ",
    )

    assert second.session_state["participant_id"] == first_id
    assert len(fake_database.participants_by_email) == 1
    assert fake_database.participants_by_email["alex@example.com"] == original
    visible = _visible_text(second)
    assert first_id not in visible
    assert first_id[-8:].upper() not in visible
    assert original.registered_at.isoformat() not in visible
    assert original.consented_at.isoformat() not in visible


def test_duplicate_email_with_material_conflict_is_neutral_and_does_not_overwrite(
    monkeypatch, fake_database
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    original = fake_database.seed_participant()
    app = AppTest.from_file("app.py").run(timeout=20)
    _fill_registration(app, full_name="Different Name")

    _button(app, "Register and continue").click().run(timeout=20)

    assert app.session_state["registration_complete"] is False
    assert app.session_state["participant_id"] is None
    assert fake_database.participants_by_email["alex@example.com"] == original
    assert len(fake_database.participants_by_email) == 1
    message = " ".join(item.value for item in app.error).lower()
    assert message
    assert "alex@example.com" not in message
    assert "alex morgan" not in message
    assert all(
        disclosure not in message
        for disclosure in ("already", "existing", "conflict", "mismatch")
    )


def test_temporary_registration_failure_keeps_gate_closed_and_can_retry(
    monkeypatch, fake_database
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    fake_database.fail_next_registration = True
    app = AppTest.from_file("app.py").run(timeout=20)
    _register(app)

    assert app.session_state["registration_complete"] is False
    assert app.session_state["participant_id"] is None
    assert app.error
    _button(app, "Register and continue").click().run(timeout=20)
    assert app.session_state["registration_complete"] is True
    assert len(fake_database.participants_by_email) == 1


def test_registration_logs_chained_database_cause_but_sanitizes_ui(
    monkeypatch,
    fake_database,
    caplog,
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def fail_with_chained_cause(**_kwargs):
        try:
            raise RuntimeError("server-only database detail")
        except RuntimeError as cause:
            raise database.DatabaseOperationError(
                "sanitized registration failure",
                retryable=True,
            ) from cause

    monkeypatch.setattr(database, "register_participant", fail_with_chained_cause)
    app = AppTest.from_file("app.py").run(timeout=20)

    with caplog.at_level(logging.ERROR):
        _register(app)

    assert "server-only database detail" in caplog.text
    assert all(
        "server-only database detail" not in item.value for item in app.error
    )
    assert app.session_state["registration_complete"] is False
    assert fake_database.participants_by_email == {}


def test_missing_supabase_configuration_fails_closed(monkeypatch, fake_database):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def missing_supabase(_secrets):
        raise database.DatabaseConfigurationError("test configuration detail")

    monkeypatch.setattr(database, "supabase_client_from_secrets", missing_supabase)
    app = AppTest.from_file("app.py").run(timeout=20)
    _register(app)

    assert app.session_state["registration_complete"] is False
    assert app.session_state["participant_id"] is None
    assert app.error
    assert all("test configuration detail" not in item.value for item in app.error)
    assert fake_database.registration_calls == []


def test_ambiguous_registration_failure_reuses_committed_participant_on_retry(
    monkeypatch, fake_database
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    fake_database.fail_after_registration_commit = True
    app = AppTest.from_file("app.py").run(timeout=20)
    _register(app)

    committed = fake_database.participants_by_email["alex@example.com"]
    assert app.session_state["registration_complete"] is False
    assert len(fake_database.participants_by_email) == 1
    _button(app, "Register and continue").click().run(timeout=20)
    assert app.session_state["participant_id"] == str(committed.participant_id)
    assert len(fake_database.participants_by_email) == 1


def test_invalid_registration_state_cannot_bypass_gate(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    participant_id = str(uuid4())
    app = AppTest.from_file("app.py")
    app.session_state["registration_complete"] = True
    app.session_state["participant_id"] = participant_id
    app.session_state["registration_receipt"] = None
    app.session_state["registration_profile"] = {
        "participant_id": participant_id,
        "name": "Alex Morgan",
        "email": "alex@example.com",
        "training_level": "Surgical resident",
        "institution": "Yarmouk University",
        "institution_number": None,
        "consent_given": True,
        "consent_version": database.CONSENT_VERSION,
    }

    app.run(timeout=20)

    assert not app.exception
    assert app.session_state["registration_complete"] is False
    assert app.session_state["participant_id"] is None
    assert app.session_state["registration_receipt"] is None
    assert app.session_state["registration_profile"] is None
    assert any(button.label == "Register and continue" for button in app.button)
    assert not any(button.label == "Start simulation" for button in app.button)


def test_invalidated_registration_receipt_clears_user_bound_case_state(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    case_id = "ali_af_embolism_iib"
    app = _complete_case(_start_specific_case(case_id), case_id)
    assert app.session_state["result_persisted"] is True
    app.session_state["registration_receipt"] = "invalid"

    app.run(timeout=20)

    assert app.session_state["registration_complete"] is False
    assert app.session_state["participant_id"] is None
    assert app.session_state["stage"] == 0
    assert app.session_state["selected_case_id"] is None
    assert app.session_state["answers"] == {}
    assert app.session_state["completed_case_ids"] == []
    assert app.session_state["result"] is None
    assert app.session_state["result_id"] is None
    assert app.session_state["result_persisted"] is False
    assert any(button.label == "Register and continue" for button in app.button)

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


def test_case_completion_inserts_correct_persistent_result(monkeypatch, fake_database):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    case_id = "ali_af_embolism_iib"
    app = _complete_case(_start_specific_case(case_id), case_id)

    assert app.session_state["result_persisted"] is True
    assert app.session_state["result_attempt_number"] == 1
    assert app.session_state["result_version_attempt_number"] == 1
    assert len(fake_database.results_by_id) == 1
    stored = next(iter(fake_database.results_by_id.values()))
    assert str(stored.participant_id) == app.session_state["participant_id"]
    assert stored.case_id == case_id
    assert stored.case_version == CASES_BY_ID[case_id].case_version
    assert stored.result_id == UUID(app.session_state["result_id"])
    assert stored.case_name == CASES_BY_ID[case_id].title
    assert stored.score == 100
    assert stored.max_score == 100
    assert str(stored.percentage) == "100.00"
    assert stored.completed_at.tzinfo is not None
    call = fake_database.result_calls[0]
    assert str(call["participant_id"]) == app.session_state["participant_id"]
    assert call["case_version"] == CASES_BY_ID[case_id].case_version
    assert "completed_at" not in call
    result_call_count = len(fake_database.result_calls)
    app.run(timeout=20)
    assert len(fake_database.result_calls) == result_call_count


def test_repeated_case_attempts_are_stored_separately(monkeypatch, fake_database):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    case_id = "symptomatic_carotid_tia"
    app = _complete_case(_start_specific_case(case_id), case_id)
    first_result_id = app.session_state["result_id"]

    _button(app, "Restart case").click().run(timeout=20)
    second_result_id = app.session_state["result_id"]
    assert second_result_id != first_result_id
    _complete_case(app, case_id)

    attempts = sorted(
        (item.attempt_number, item.version_attempt_number)
        for item in fake_database.results_by_id.values()
        if item.case_id == case_id
    )
    assert attempts == [(1, 1), (2, 2)]
    assert len(fake_database.results_by_id) == 2


def test_ambiguous_result_failure_retries_idempotently(monkeypatch, fake_database):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    fake_database.fail_after_result_commit = True
    case_id = "ruptured_infrarenal_aaa"
    app = _complete_case(_start_specific_case(case_id), case_id)
    result_id = app.session_state["result_id"]

    assert app.session_state["result_persisted"] is False
    assert len(fake_database.results_by_id) == 1
    assert any("not been saved yet" in item.value for item in app.warning)
    assert all(
        button.disabled
        for button in app.button
        if button.label in {"Restart case", "New vascular case"}
    )

    _button(app, "Retry saving result").click().run(timeout=20)

    assert app.session_state["result_id"] == result_id
    assert app.session_state["result_persisted"] is True
    assert app.session_state["result_attempt_number"] == 1
    assert app.session_state["result_version_attempt_number"] == 1
    assert len(fake_database.results_by_id) == 1
    assert [call["result_id"] for call in fake_database.result_calls] == [
        UUID(result_id),
        UUID(result_id),
    ]


def test_result_failure_before_commit_retries_same_result_id(monkeypatch, fake_database):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    fake_database.fail_next_result_save = True
    case_id = "iliofemoral_dvt_phlegmasia"
    app = _complete_case(_start_specific_case(case_id), case_id)
    result_id = app.session_state["result_id"]

    assert app.session_state["result_persisted"] is False
    assert fake_database.results_by_id == {}
    _button(app, "Retry saving result").click().run(timeout=20)

    assert app.session_state["result_persisted"] is True
    assert app.session_state["result_id"] == result_id
    assert len(fake_database.results_by_id) == 1
    assert [call["result_id"] for call in fake_database.result_calls] == [
        UUID(result_id),
        UUID(result_id),
    ]


def test_permanent_supabase_result_error_points_to_migration_without_claiming_outage(
    monkeypatch,
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    case_id = "penetrating_femoral_artery_trauma"
    app = _start_specific_case(case_id)

    def reject_result(**_kwargs):
        raise database.DatabaseOperationError("safe test rejection", retryable=False)

    monkeypatch.setattr(database, "save_case_result", reject_result)
    app = _complete_case(app, case_id)

    assert app.session_state["result_persisted"] is False
    warning_text = " ".join(item.value for item in app.warning)
    assert "migration and RPC permissions" in warning_text
    assert "temporarily unavailable" not in warning_text


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
    first_orders = {
        question_id: list(option_ids)
        for question_id, option_ids in app.session_state["option_orders"].items()
    }
    correct = next(option.option_id for option in first_stage.question.options if option.option_id in case.correct_actions)
    _widget(app.radio, first_stage.question.prompt).set_value(correct)
    _button(app, "Lock answer and continue").click().run(timeout=20)

    _button(app, "Restart case").click().run(timeout=20)

    assert app.session_state["stage"] == 1
    assert app.session_state["selected_case_id"] == case.case_id
    assert app.session_state["answers"] == {}
    assert _widget(app.radio, first_stage.question.prompt).value is None
    assert any(button.label == "New vascular case" for button in app.button)
    restarted_orders = app.session_state["option_orders"]
    for stage in case.stages:
        question_id = stage.question.question_id
        correct_id = next(
            option.option_id
            for option in stage.question.options
            if option.option_id in case.correct_actions
        )
        assert restarted_orders[question_id].index(correct_id) != first_orders[question_id].index(correct_id)


def test_choices_display_as_randomized_lettered_options(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    case = CASES_BY_ID["ali_af_embolism_iib"]
    app = _start_specific_case(case.case_id)
    question = case.stages[0].question
    radio = _widget(app.radio, question.prompt)

    assert [option[:2] for option in radio.options] == ["A.", "B.", "C.", "D."]
    correct_id = next(
        option.option_id
        for option in question.options
        if option.option_id in case.correct_actions
    )
    correct_position = app.session_state["option_orders"][question.question_id].index(correct_id)
    assert case.option_labels[correct_id] in radio.options[correct_position]


def test_new_case_workflow_preserves_history_and_returns_to_landing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    case_id = "penetrating_femoral_artery_trauma"
    app = _complete_case(_start_specific_case(case_id), case_id)
    participant_id = app.session_state["participant_id"]

    _button(app, "New vascular case").click().run(timeout=20)

    assert app.session_state["stage"] == 0
    assert app.session_state["selected_case_id"] is None
    assert case_id in app.session_state["completed_case_ids"]
    assert app.session_state["previous_case_id"] == case_id
    assert app.session_state["participant_id"] == participant_id
    assert any(button.label == "Start simulation" for button in app.button)


def test_incomplete_report_state_recovers_to_landing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = _register(AppTest.from_file("app.py").run(timeout=20))
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
