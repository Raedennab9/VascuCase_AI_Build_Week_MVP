from __future__ import annotations

import html
import logging
import secrets
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import streamlit as st

from vascucase import database
from vascucase.cases.library import (
    CASE_MODES,
    CASES,
    CASES_BY_ID,
    CATEGORIES,
    select_case,
)
from vascucase.cases.schema import Question, VascularCase
from vascucase.feedback import generate_feedback
from vascucase.presentation import build_option_orders, valid_option_orders
from vascucase.reporting import build_report_json
from vascucase.scoring import score_case


st.set_page_config(
    page_title="VascuCase AI",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="auto",
)

CSS = """
<style>
:root {
  --vc-navy: #0b2742;
  --vc-blue: #164e75;
  --vc-red: #a61b29;
  --vc-slate: #475569;
  --vc-border: #cbd5e1;
  --vc-surface: #f8fafc;
}
.block-container {max-width: 1120px; padding-top: 1.4rem;}
.vc-hero {
  background: linear-gradient(120deg, var(--vc-navy), var(--vc-blue));
  color: white; padding: 1.55rem 1.8rem; border-radius: 18px; margin-bottom: 1rem;
}
.vc-kicker {letter-spacing: .09em; text-transform: uppercase; font-size: .78rem; opacity: .84;}
.vc-badges {display: flex; flex-wrap: wrap; gap: .45rem; margin: .2rem 0 .85rem;}
.vc-badge {
  display: inline-block; border: 1px solid #94a3b8; border-radius: 999px;
  padding: .2rem .62rem; color: #334155; background: #f8fafc; font-size: .82rem;
}
.vc-registration-lead {font-size: 1.04rem; color: var(--vc-slate); margin-bottom: 1rem;}
.vc-registration-card {
  border: 1px solid var(--vc-border); border-radius: 16px; background: var(--vc-surface);
  padding: 1.05rem 1.15rem; margin: .35rem 0 1rem;
}
.vc-registration-card strong {color: var(--vc-navy);}
.vc-registration-card ul {margin: .6rem 0 .15rem; padding-left: 1.15rem;}
.vc-registration-card li {margin-bottom: .42rem;}
.vc-privacy-note {
  border-left: 4px solid var(--vc-blue); border-radius: 10px; background: #eef6fb;
  color: #243b53; padding: .85rem 1rem; margin: .8rem 0 1rem;
}
.vc-privacy-note strong {color: var(--vc-navy);}
.vc-session-label {color: #64748b; font-size: .8rem; letter-spacing: .02em;}
*:focus-visible {outline: 3px solid #f59e0b !important; outline-offset: 3px;}
@media (max-width: 700px) {
  .block-container {padding: .8rem 1rem 2rem;}
  .vc-hero {padding: 1.05rem 1.1rem; border-radius: 13px;}
  .vc-hero h1 {font-size: 1.9rem !important;}
  .vc-hero p {font-size: .98rem !important;}
  .vc-registration-card {padding: .9rem 1rem; border-radius: 13px;}
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {scroll-behavior: auto !important; transition: none !important; animation: none !important;}
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


LOGGER = logging.getLogger(__name__)
FULL_NAME_MAX_LENGTH = 120
TRAINING_LEVELS = database.TRAINING_LEVELS
CONSENT_VERSION = database.CONSENT_VERSION


def _registration_errors(
    *,
    full_name: str,
    email: str,
    training_level: str | None,
    institution: str,
    institution_number: str,
    privacy_acknowledged: bool,
) -> list[str]:
    errors: list[str] = []
    try:
        database.normalize_name(full_name)
    except ValueError as exc:
        errors.append(str(exc))
    try:
        database.normalize_email(email)
    except ValueError as exc:
        errors.append(str(exc))
    try:
        normalized_level = database.normalize_training_level(training_level)
    except (TypeError, ValueError) as exc:
        errors.append(str(exc))
        normalized_level = None
    try:
        database.normalize_institution(institution)
    except (TypeError, ValueError) as exc:
        errors.append(str(exc))
    if normalized_level is not None:
        try:
            database.normalize_institution_number(
                institution_number,
                training_level=normalized_level,
            )
        except (TypeError, ValueError) as exc:
            errors.append(str(exc))
    if not privacy_acknowledged:
        errors.append("Read and accept the privacy and data-use notice to continue.")
    return errors


def _valid_registration_profile(profile: Any) -> bool:
    if not isinstance(profile, dict):
        return False
    try:
        normalized_name = database.normalize_name(profile.get("name", ""))
        normalized_email = database.normalize_email(profile.get("email", ""))
        normalized_institution = database.normalize_institution(
            profile.get("institution", "")
        )
        normalized_number = database.normalize_institution_number(
            profile.get("institution_number"),
            training_level=profile.get("training_level"),
        )
    except (TypeError, ValueError):
        return False
    return all(
        (
            _valid_uuid(profile.get("participant_id")),
            profile.get("name") == normalized_name,
            profile.get("email") == normalized_email,
            profile.get("training_level") in TRAINING_LEVELS,
            profile.get("institution") == normalized_institution,
            profile.get("institution_number") == normalized_number,
            profile.get("consent_given") is True,
            profile.get("consent_version") == CONSENT_VERSION,
        )
    )


def _valid_uuid(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        UUID(value)
    except (ValueError, AttributeError):
        return False
    return True


def _reset_case_progress() -> None:
    st.session_state.stage = 0
    st.session_state.answers = {}
    st.session_state.option_orders = {}
    st.session_state.last_option_orders = {}
    st.session_state.selected_case_id = None
    st.session_state.result = None
    st.session_state.result_id = None
    st.session_state.result_persisted = False
    st.session_state.result_attempt_number = None
    st.session_state.result_version_attempt_number = None
    st.session_state.result_persistence_error = None
    st.session_state.feedback = None
    st.session_state.completion_timestamp = None
    st.session_state.completed_case_ids = []
    st.session_state.previous_case_id = None
    st.session_state.learner_level = TRAINING_LEVELS[1]
    st.session_state.safety_identifier = secrets.token_hex(16)
    for key in list(st.session_state):
        if str(key).startswith("answer_"):
            del st.session_state[key]


def _clear_registration_state() -> None:
    st.session_state.registration_complete = False
    st.session_state.participant_id = None
    st.session_state.registration_profile = None
    st.session_state.registration_receipt = None
    _reset_case_progress()
    registration_widget_keys = {
        "registration_email",
        "registration_full_name",
        "registration_training_level",
        "registration_institution",
        "registration_institution_number",
        "registration_privacy_acknowledged",
    }
    for key in registration_widget_keys:
        st.session_state.pop(key, None)


def _activate_participant(
    participant: database.ParticipantRecord,
    *,
    name: str,
    email: str,
    training_level: str,
    institution: str,
    institution_number: str | None,
) -> None:
    normalized_name = database.normalize_name(name)
    normalized_email = database.normalize_email(email)
    normalized_level = database.normalize_training_level(training_level)
    normalized_institution = database.normalize_institution(institution)
    normalized_number = database.normalize_institution_number(
        institution_number,
        training_level=normalized_level,
    )
    if (
        participant.name != normalized_name
        or participant.email != normalized_email
        or participant.training_level != normalized_level
        or participant.institution != normalized_institution
        or participant.institution_number != normalized_number
        or participant.consent_given is not True
        or participant.consent_version != CONSENT_VERSION
    ):
        raise database.DatabaseOperationError(
            "Supabase returned a mismatched participant registration."
        )
    profile = {
        "participant_id": str(participant.participant_id),
        "name": normalized_name,
        "email": normalized_email,
        "training_level": normalized_level,
        "institution": normalized_institution,
        "institution_number": normalized_number,
        "consent_given": True,
        "consent_version": CONSENT_VERSION,
    }
    if not _valid_registration_profile(profile):
        raise database.DatabaseOperationError(
            "Supabase returned an incomplete participant profile."
        )
    st.session_state.participant_id = str(participant.participant_id)
    st.session_state.registration_profile = profile
    st.session_state.learner_level = normalized_level
    st.session_state.registration_receipt = secrets.token_hex(32)
    st.session_state.registration_complete = True


def _valid_registration_receipt(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _registration_session_is_valid() -> bool:
    profile = st.session_state.get("registration_profile")
    return all(
        (
            st.session_state.get("registration_complete") is True,
            _valid_registration_profile(profile),
            isinstance(profile, dict)
            and profile.get("participant_id") == st.session_state.get("participant_id"),
            isinstance(profile, dict)
            and profile.get("training_level") == st.session_state.get("learner_level"),
            _valid_registration_receipt(
                st.session_state.get("registration_receipt")
            ),
        )
    )


def init_state() -> None:
    defaults: dict[str, Any] = {
        "registration_complete": False,
        "participant_id": None,
        "registration_profile": None,
        "registration_receipt": None,
        "stage": 0,
        "answers": {},
        "option_orders": {},
        "last_option_orders": {},
        "selected_case_id": None,
        "result": None,
        "result_id": None,
        "result_persisted": False,
        "result_attempt_number": None,
        "result_version_attempt_number": None,
        "result_persistence_error": None,
        "feedback": None,
        "completion_timestamp": None,
        "learner_level": TRAINING_LEVELS[1],
        "case_mode": CASE_MODES[0],
        "selected_category": CATEGORIES[0],
        "specific_case_id": CASES[0].case_id,
        "completed_case_ids": [],
        "previous_case_id": None,
        "safety_identifier": secrets.token_hex(16),
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    if not isinstance(st.session_state.result_persisted, bool):
        st.session_state.result_persisted = False
    if not isinstance(st.session_state.result_attempt_number, (int, type(None))):
        st.session_state.result_attempt_number = None
    if not isinstance(
        st.session_state.result_version_attempt_number,
        (int, type(None)),
    ):
        st.session_state.result_version_attempt_number = None
    if not isinstance(st.session_state.result_persistence_error, (str, type(None))):
        st.session_state.result_persistence_error = None

    if not isinstance(st.session_state.answers, dict):
        st.session_state.answers = {}
    if not isinstance(st.session_state.option_orders, dict):
        st.session_state.option_orders = {}
    if not isinstance(st.session_state.last_option_orders, dict):
        st.session_state.last_option_orders = {}
    if not isinstance(st.session_state.completed_case_ids, list):
        st.session_state.completed_case_ids = []
    st.session_state.completed_case_ids = list(
        dict.fromkeys(
            case_id
            for case_id in st.session_state.completed_case_ids
            if case_id in CASES_BY_ID
        )
    )
    if st.session_state.stage not in range(6):
        st.session_state.stage = 0
    if st.session_state.selected_case_id not in CASES_BY_ID:
        st.session_state.selected_case_id = None
        if st.session_state.stage > 0:
            _clear_attempt(stage=0)
    elif st.session_state.stage > 0:
        selected_case = CASES_BY_ID[st.session_state.selected_case_id]
        if not valid_option_orders(selected_case, st.session_state.option_orders):
            _set_new_option_orders(selected_case)
    if st.session_state.stage in range(1, 5) and not _valid_uuid(st.session_state.result_id):
        st.session_state.result_id = str(uuid4())
    if st.session_state.stage == 5 and (
        not isinstance(st.session_state.result, dict)
        or not isinstance(st.session_state.feedback, dict)
        or not st.session_state.completion_timestamp
        or not _valid_uuid(st.session_state.result_id)
    ):
        _clear_attempt(stage=0, clear_case=True)


def _clear_widget_answers() -> None:
    for key in list(st.session_state):
        if str(key).startswith("answer_"):
            del st.session_state[key]


def _clear_attempt(*, stage: int, clear_case: bool = False) -> None:
    st.session_state.stage = stage
    st.session_state.answers = {}
    st.session_state.option_orders = {}
    st.session_state.result = None
    st.session_state.result_id = str(uuid4()) if stage in range(1, 5) else None
    st.session_state.result_persisted = False
    st.session_state.result_attempt_number = None
    st.session_state.result_version_attempt_number = None
    st.session_state.result_persistence_error = None
    st.session_state.feedback = None
    st.session_state.completion_timestamp = None
    if clear_case:
        st.session_state.selected_case_id = None
    _clear_widget_answers()


def restart_case() -> None:
    if st.session_state.selected_case_id in CASES_BY_ID:
        case = CASES_BY_ID[st.session_state.selected_case_id]
        _clear_attempt(stage=1)
        _set_new_option_orders(case)
    else:
        _clear_attempt(stage=0, clear_case=True)


def new_case() -> None:
    _clear_attempt(stage=0, clear_case=True)


def current_case() -> VascularCase | None:
    case_id = st.session_state.selected_case_id
    return CASES_BY_ID.get(case_id)


def _set_new_option_orders(case: VascularCase) -> None:
    previous = st.session_state.last_option_orders.get(case.case_id)
    if not valid_option_orders(case, previous):
        previous = None
    orders = build_option_orders(case, previous_orders=previous)
    st.session_state.option_orders = orders
    st.session_state.last_option_orders[case.case_id] = orders


def begin_case() -> None:
    case, normalized_history = select_case(
        mode=st.session_state.case_mode,
        completed_case_ids=st.session_state.completed_case_ids,
        previous_case_id=st.session_state.previous_case_id,
        category=st.session_state.selected_category,
        specific_case_id=st.session_state.specific_case_id,
    )
    _clear_attempt(stage=1)
    st.session_state.completed_case_ids = sorted(normalized_history)
    st.session_state.selected_case_id = case.case_id
    st.session_state.previous_case_id = case.case_id
    _set_new_option_orders(case)


def render_badges(case: VascularCase) -> None:
    st.markdown(
        '<div class="vc-badges">'
        f'<span class="vc-badge">Category: {html.escape(case.category)}</span>'
        f'<span class="vc-badge">Difficulty: {html.escape(case.difficulty)}</span>'
        "</div>",
        unsafe_allow_html=True,
    )


def render_question(case: VascularCase, question: Question) -> Any:
    labels = case.option_labels
    option_ids = st.session_state.option_orders[question.question_id]
    displayed_labels = {
        option_id: f"{chr(65 + index)}. {labels[option_id]}"
        for index, option_id in enumerate(option_ids)
    }
    key = f"answer_{case.case_id}_{question.question_id}"
    if question.kind == "single":
        return st.radio(
            question.prompt,
            option_ids,
            format_func=displayed_labels.__getitem__,
            index=None,
            key=key,
        )
    return st.multiselect(
        question.prompt,
        option_ids,
        format_func=displayed_labels.__getitem__,
        key=key,
    )


def answer_is_valid(question: Question, answer: Any) -> bool:
    if question.kind == "single":
        return isinstance(answer, str)
    return isinstance(answer, list) and len(answer) >= question.min_selections


def finish_case(case: VascularCase) -> None:
    result = score_case(case, st.session_state.answers)
    st.session_state.result = result
    with st.spinner("Preparing educational feedback..."):
        st.session_state.feedback = generate_feedback(
            case=case,
            result=result,
            learner_level=st.session_state.learner_level,
            safety_identifier=st.session_state.safety_identifier,
        )
    completed = set(st.session_state.completed_case_ids)
    completed.add(case.case_id)
    st.session_state.completed_case_ids = sorted(completed)
    st.session_state.completion_timestamp = datetime.now(timezone.utc).isoformat()
    st.session_state.stage = 5
    persist_current_result(case)


def persist_current_result(case: VascularCase) -> bool:
    if st.session_state.result_persisted:
        return True
    if not _valid_uuid(st.session_state.result_id):
        st.session_state.result_id = str(uuid4())

    try:
        saved = database.save_case_result(
            client=database.supabase_client_from_secrets(st.secrets),
            result_id=st.session_state.result_id,
            participant_id=st.session_state.participant_id,
            case_id=case.case_id,
            case_version=case.case_version,
            case_name=case.title,
            score=st.session_state.result["score"],
            max_score=st.session_state.result["max_score"],
        )
    except database.DatabaseError as exc:
        LOGGER.exception(
            "Case-result persistence failed (%s)", type(exc).__name__
        )
        st.session_state.result_persisted = False
        st.session_state.result_attempt_number = None
        st.session_state.result_version_attempt_number = None
        if isinstance(exc, database.DatabaseOperationError) and exc.retryable:
            st.session_state.result_persistence_error = (
                "Your score is available, but it has not been saved yet. "
                "The Supabase connection is temporarily unavailable; retry in a moment."
            )
        else:
            st.session_state.result_persistence_error = (
                "Your score is available, but it has not been saved. Ask the app operator "
                "to verify the Supabase migration and RPC permissions before retrying."
            )
        return False

    st.session_state.result_persisted = True
    st.session_state.result_attempt_number = saved.attempt_number
    st.session_state.result_version_attempt_number = saved.version_attempt_number
    st.session_state.completion_timestamp = saved.completed_at.isoformat()
    st.session_state.result_persistence_error = None
    return True


def render_hero() -> None:
    st.markdown(
        """
        <div class="vc-hero">
          <div class="vc-kicker">OpenAI Build Week prototype</div>
          <h1 style="margin:.25rem 0 .45rem 0;">VascuCase AI</h1>
          <p style="margin:0; font-size:1.08rem;">Eight progressive vascular cases. Deterministic clinical scoring. Adaptive explanation.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _end_session_and_clear() -> None:
    _clear_registration_state()


def render_registration() -> None:
    render_hero()
    st.caption("Fictional educational cases only. Do not enter or use real patient information.")

    intro_col, form_col = st.columns([1, 1.15], gap="large")
    with intro_col:
        st.subheader("Learn through clinical decisions")
        st.markdown(
            '<p class="vc-registration-lead">Create or resume your persistent '
            "participant profile, then enter the vascular case library.</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="vc-registration-card">
              <strong>What to expect</strong>
              <ul>
                <li>One registration form with persistent Supabase storage</li>
                <li>Four sequential decisions in each fictional case</li>
                <li>Deterministic scoring and safety-focused feedback</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.warning(
            "**Education only.** VascuCase AI is not a diagnostic or treatment "
            "tool and must not be used for real-time patient care."
        )

    with form_col:
        st.subheader("Participant registration")
        st.caption(
            "Email is used for record matching only. This form does not verify "
            "email ownership or provide account authentication."
        )
        with st.form("participant_registration_form"):
            full_name = st.text_input(
                "Full name *",
                max_chars=FULL_NAME_MAX_LENGTH,
                placeholder="e.g., Raed Ennab",
                key="registration_full_name",
            )
            email = st.text_input(
                "Email address *",
                max_chars=254,
                placeholder="e.g., learner@example.com",
                help="Surrounding whitespace is removed and matching uses lowercase.",
                key="registration_email",
            )
            institution = st.text_input(
                "Institution / University *",
                placeholder="e.g., Yarmouk University",
                key="registration_institution",
            )
            institution_number = st.text_input(
                "University / Institutional Number (required for Medical students)",
                placeholder="Text such as 00123-A is preserved",
                key="registration_institution_number",
            )
            training_level = st.selectbox(
                "Current training level *",
                (None, *TRAINING_LEVELS),
                index=0,
                format_func=lambda value: (
                    "Select your training level" if value is None else value
                ),
                key="registration_training_level",
            )
            st.markdown(
                """
                <div class="vc-privacy-note">
                  <strong>Privacy and data use</strong><br>
                  VascuCase stores your name, email, training level,
                  institution, institutional number when supplied, consent record,
                  and case performance. These operational data are identifiable.
                  Research exports may be de-identified or pseudonymized, but they
                  are not anonymous. Do not enter patient information.
                </div>
                """,
                unsafe_allow_html=True,
            )
            privacy_acknowledged = st.checkbox(
                "I consent to the storage and use described above and understand "
                "that VascuCase AI is for education only—not patient care. *",
                key="registration_privacy_acknowledged",
            )
            submitted = st.form_submit_button(
                "Register and continue",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            errors = _registration_errors(
                full_name=full_name,
                email=email,
                training_level=training_level,
                institution=institution,
                institution_number=institution_number,
                privacy_acknowledged=privacy_acknowledged,
            )
            if errors:
                for error in errors:
                    st.error(error)
            else:
                try:
                    participant = database.register_participant(
                        client=database.supabase_client_from_secrets(st.secrets),
                        name=full_name,
                        email=email,
                        training_level=training_level,
                        institution=institution,
                        institution_number=institution_number,
                        consent_given=True,
                    )
                    _activate_participant(
                        participant,
                        name=full_name,
                        email=email,
                        training_level=training_level,
                        institution=institution,
                        institution_number=institution_number,
                    )
                except database.DatabaseConfigurationError as exc:
                    LOGGER.exception(
                        "Participant registration configuration failed: %s",
                        type(exc).__name__,
                    )
                    st.error(
                        "Registration is not configured. Ask the app operator to "
                        "set SUPABASE_URL and SUPABASE_SECRET_KEY."
                    )
                except database.DatabaseOperationError as exc:
                    LOGGER.exception(
                        "Participant registration failed: %s", type(exc).__name__
                    )
                    if exc.retryable:
                        st.error(
                            "Registration could not be saved because the database is "
                            "temporarily unavailable. Try again in a moment."
                        )
                    else:
                        st.error(
                            "Registration could not be completed. Check your "
                            "registration information and try again."
                        )
                except database.DatabaseError as exc:
                    LOGGER.exception(
                        "Participant registration failed: %s", type(exc).__name__
                    )
                    st.error(
                        "Registration could not be completed. Check your "
                        "registration information and try again."
                    )
                except ValueError as exc:
                    LOGGER.warning(
                        "Participant registration validation failed: %s",
                        type(exc).__name__,
                    )
                    st.error(
                        "Registration could not be completed. Check your "
                        "registration information and try again."
                    )
                else:
                    st.rerun()

    st.divider()
    st.caption(
        "VascuCase AI is a Build Week educational prototype. Clinical content "
        "is simplified and requires expert curricular review before deployment."
    )


init_state()
if st.session_state.registration_complete and not _registration_session_is_valid():
    _clear_registration_state()
if not _registration_session_is_valid():
    render_registration()
    st.stop()

case = current_case()

with st.sidebar:
    st.title("VascuCase AI")
    st.caption("Multi-case vascular-surgery simulation")
    profile = st.session_state.registration_profile
    st.caption(f"Welcome, {profile['name']}")
    st.markdown(
        '<span class="vc-session-label">Registered session</span>',
        unsafe_allow_html=True,
    )
    if st.button("End session", use_container_width=True):
        _end_session_and_clear()
        st.rerun()
    st.divider()
    st.selectbox(
        "Learner level",
        TRAINING_LEVELS,
        key="learner_level",
        disabled=True,
        help="Training level is set during persistent registration.",
    )
    visible_stage = min(max(st.session_state.stage, 0), 4) if case else 0
    st.progress(visible_stage / 4, text=f"Case progress: {visible_stage}/4")
    st.caption(f"Completed case counter: {len(st.session_state.completed_case_ids)}/{len(CASES)}")
    if case:
        st.divider()
        st.markdown("**Case in progress**")
        st.write(case.title)
        st.caption(f"{case.category} · {case.difficulty}")
        unsaved_completion = st.session_state.stage == 5 and not st.session_state.result_persisted
        if st.button(
            "Restart case",
            use_container_width=True,
            disabled=unsaved_completion,
            help="Save or retry the completed result before restarting." if unsaved_completion else None,
        ):
            restart_case()
            st.rerun()
        if st.session_state.stage < 5 and st.button("New vascular case", use_container_width=True):
            new_case()
            st.rerun()
    st.divider()
    st.warning(
        "**Education only.** Every case is fictional. This is not a diagnostic or treatment tool and is not for real-time patient care."
    )

render_hero()
st.caption("Fictional educational cases only. Do not enter or use real patient information.")

if st.session_state.stage == 0:
    st.subheader("Choose your simulation")
    st.write(
        "Work through four sequential decisions. The final diagnosis and expert pathway remain concealed until submission."
    )
    st.radio("Case mode", CASE_MODES, key="case_mode")
    if st.session_state.case_mode == "Random vascular case":
        st.info(
            "Random mode draws from all eight cases, avoids an immediate repeat, and resets its completed-case history after every eligible case has been completed."
        )
    elif st.session_state.case_mode == "Choose category":
        st.selectbox("Case category", CATEGORIES, key="selected_category")
        eligible_count = sum(case.category == st.session_state.selected_category for case in CASES)
        st.caption(f"{eligible_count} case(s) available in this category; selection is random within the category.")
    else:
        st.selectbox(
            "Specific case",
            [item.case_id for item in CASES],
            format_func=lambda case_id: CASES_BY_ID[case_id].title,
            key="specific_case_id",
        )
    left, right = st.columns([1.3, 1])
    with left:
        st.markdown(
            "**What is assessed**\n\n"
            "- Initial recognition and focused assessment\n"
            "- Severity, classification, or anatomical interpretation\n"
            "- Investigations and immediate management\n"
            "- Definitive management and escalation"
        )
        st.info(
            "The 100-point score, unsafe flags, expert pathway, and final diagnosis are authored and calculated outside the language model."
        )
        if st.button("Start simulation", type="primary", use_container_width=True):
            begin_case()
            st.rerun()
    with right:
        with st.container(border=True):
            st.metric("Case library", f"{len(CASES)} cases")
            st.metric("Decision stages", "4 per case")
            st.metric("Maximum score", "100")
            st.markdown("**Public mode:** fully functional without an API key")

elif st.session_state.stage in range(1, 5) and case:
    stage_number = st.session_state.stage
    stage = case.stages[stage_number - 1]
    st.caption(f"Case {len(st.session_state.completed_case_ids) + 1} · Stage {stage_number} of 4")
    st.subheader(stage.title)
    render_badges(case)
    with st.container(border=True):
        if stage_number == 1:
            st.write(case.brief_presentation)
        st.write(stage.content)

    submit_labels = {
        1: "Lock answer and continue",
        2: "Lock answer and continue",
        3: "Lock answer and continue",
        4: "Submit case for scoring",
    }
    with st.form(f"case_stage_{stage_number}"):
        answer = render_question(case, stage.question)
        submitted = st.form_submit_button(submit_labels[stage_number], type="primary")
    if submitted:
        if not answer_is_valid(stage.question, answer):
            st.error("Select an answer before continuing.")
        else:
            st.session_state.answers[stage.question.question_id] = answer
            if stage_number < 4:
                st.session_state.stage += 1
            else:
                finish_case(case)
            st.rerun()

elif st.session_state.stage == 5 and case:
    result = st.session_state.result
    feedback = st.session_state.feedback
    st.subheader("Performance report")
    render_badges(case)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total score", f"{result['score']}/{result['max_score']}")
    col2.metric("Performance band", result["band"])
    col3.metric("Critical omissions", len(result["critical_omissions"]))
    st.progress(result["score"] / result["max_score"])

    if st.session_state.result_persisted:
        st.success(
            "Result saved as overall attempt "
            f"{st.session_state.result_attempt_number} and case-version attempt "
            f"{st.session_state.result_version_attempt_number}."
        )
    else:
        st.warning(st.session_state.result_persistence_error or "This result has not been saved yet.")
        if st.button("Retry saving result", key="retry_result_save"):
            persist_current_result(case)
            st.rerun()

    st.markdown("### Final diagnosis")
    st.success(case.final_diagnosis)

    left, right = st.columns(2)
    with left:
        st.markdown("### Correct actions")
        if result["correct_actions"]:
            for item in result["correct_actions"]:
                st.success(item)
        else:
            st.info("No scored action was selected.")
    with right:
        st.markdown("### Priority corrections")
        if result["critical_omissions"]:
            for item in result["critical_omissions"]:
                st.error(item)
        else:
            st.success("No critical action was omitted.")
        for item in result["unsafe_selections"]:
            st.warning(f"Unsafe selection: {item['action']} — {item['explanation']}")

    st.markdown("### Domain scores")
    for domain, data in result["domain_scores"].items():
        st.write(f"**{domain}:** {data['score']}/{data['max_score']}")
        if data["unsafe_penalty"]:
            st.caption(f"Unsafe-choice penalty recorded in this domain: {data['unsafe_penalty']}")

    st.markdown("### Educational feedback")
    st.info(
        "The deterministic score, omissions, unsafe flags, expert pathway, and final diagnosis are authoritative and cannot be altered by generated prose."
    )
    st.write(feedback["text"])
    st.caption(f"Feedback source: {feedback['source']}")

    with st.expander("Expert pathway", expanded=True):
        for number, item in enumerate(case.model_pathway, start=1):
            st.markdown(f"**{number}.** {item}")

    with st.expander("Take-home learning points"):
        for item in case.learning_points:
            st.markdown(f"- {item}")

    with st.expander("Evidence references"):
        for reference in case.references:
            st.markdown(f"- [{reference.citation}]({reference.url})")

    report_json = build_report_json(
        case=case,
        learner_level=st.session_state.learner_level,
        result=result,
        feedback_source=feedback["source"],
        completion_timestamp=st.session_state.completion_timestamp,
    )
    st.download_button(
        "Download performance report (JSON)",
        data=report_json,
        file_name=f"vascucase_{case.case_id}_report.json",
        mime="application/json",
        help="Downloads this fictional simulation attempt without free text or identifiers.",
        on_click="ignore",
        use_container_width=True,
    )

    restart_col, new_col = st.columns(2)
    result_navigation_disabled = not st.session_state.result_persisted
    if restart_col.button(
        "Restart case",
        use_container_width=True,
        key="report_restart",
        disabled=result_navigation_disabled,
        help="Save or retry this result before restarting." if result_navigation_disabled else None,
    ):
        restart_case()
        st.rerun()
    if new_col.button(
        "New vascular case",
        type="primary",
        use_container_width=True,
        key="report_new",
        disabled=result_navigation_disabled,
        help="Save or retry this result before starting another case."
        if result_navigation_disabled
        else None,
    ):
        new_case()
        st.rerun()

st.divider()
st.caption(
    "VascuCase AI is a Build Week educational prototype. Clinical content is simplified and requires expert curricular review before deployment."
)
