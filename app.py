from __future__ import annotations

import html
import secrets
from datetime import datetime, timezone
from typing import Any

import streamlit as st

from vascucase.cases.library import (
    CASE_MODES,
    CASES,
    CASES_BY_ID,
    CATEGORIES,
    LEARNER_LEVELS,
    select_case,
)
from vascucase.cases.schema import Question, VascularCase
from vascucase.feedback import generate_feedback
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
*:focus-visible {outline: 3px solid #f59e0b !important; outline-offset: 3px;}
@media (max-width: 700px) {
  .block-container {padding: .8rem 1rem 2rem;}
  .vc-hero {padding: 1.05rem 1.1rem; border-radius: 13px;}
  .vc-hero h1 {font-size: 1.9rem !important;}
  .vc-hero p {font-size: .98rem !important;}
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {scroll-behavior: auto !important; transition: none !important; animation: none !important;}
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def init_state() -> None:
    defaults: dict[str, Any] = {
        "stage": 0,
        "answers": {},
        "selected_case_id": None,
        "result": None,
        "feedback": None,
        "completion_timestamp": None,
        "learner_level": LEARNER_LEVELS[1],
        "case_mode": CASE_MODES[0],
        "selected_category": CATEGORIES[0],
        "specific_case_id": CASES[0].case_id,
        "completed_case_ids": [],
        "previous_case_id": None,
        "safety_identifier": secrets.token_hex(16),
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    if not isinstance(st.session_state.answers, dict):
        st.session_state.answers = {}
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
    if st.session_state.stage == 5 and (
        not isinstance(st.session_state.result, dict)
        or not isinstance(st.session_state.feedback, dict)
        or not st.session_state.completion_timestamp
    ):
        _clear_attempt(stage=0, clear_case=True)


def _clear_widget_answers() -> None:
    for key in list(st.session_state):
        if str(key).startswith("answer_"):
            del st.session_state[key]


def _clear_attempt(*, stage: int, clear_case: bool = False) -> None:
    st.session_state.stage = stage
    st.session_state.answers = {}
    st.session_state.result = None
    st.session_state.feedback = None
    st.session_state.completion_timestamp = None
    if clear_case:
        st.session_state.selected_case_id = None
    _clear_widget_answers()


def restart_case() -> None:
    if st.session_state.selected_case_id in CASES_BY_ID:
        _clear_attempt(stage=1)
    else:
        _clear_attempt(stage=0, clear_case=True)


def new_case() -> None:
    _clear_attempt(stage=0, clear_case=True)


def current_case() -> VascularCase | None:
    case_id = st.session_state.selected_case_id
    return CASES_BY_ID.get(case_id)


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
    option_ids = [option.option_id for option in question.options]
    key = f"answer_{case.case_id}_{question.question_id}"
    if question.kind == "single":
        return st.radio(
            question.prompt,
            option_ids,
            format_func=labels.__getitem__,
            index=None,
            key=key,
        )
    return st.multiselect(
        question.prompt,
        option_ids,
        format_func=labels.__getitem__,
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


init_state()
case = current_case()

with st.sidebar:
    st.title("VascuCase AI")
    st.caption("Multi-case vascular-surgery simulation")
    st.selectbox(
        "Learner level",
        LEARNER_LEVELS,
        key="learner_level",
        disabled=st.session_state.stage > 0,
    )
    visible_stage = min(max(st.session_state.stage, 0), 4) if case else 0
    st.progress(visible_stage / 4, text=f"Case progress: {visible_stage}/4")
    st.caption(f"Completed case counter: {len(st.session_state.completed_case_ids)}/{len(CASES)}")
    if case:
        st.divider()
        st.markdown("**Case in progress**")
        st.write(case.title)
        st.caption(f"{case.category} · {case.difficulty}")
        if st.button("Restart case", use_container_width=True):
            restart_case()
            st.rerun()
        if st.session_state.stage < 5 and st.button("New vascular case", use_container_width=True):
            new_case()
            st.rerun()
    st.divider()
    st.warning(
        "**Education only.** Every case is fictional. This is not a diagnostic or treatment tool and is not for real-time patient care."
    )

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
    col1.metric("Total score", f"{result['score']}/100")
    col2.metric("Performance band", result["band"])
    col3.metric("Critical omissions", len(result["critical_omissions"]))
    st.progress(result["score"] / 100)

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
    if restart_col.button("Restart case", use_container_width=True, key="report_restart"):
        restart_case()
        st.rerun()
    if new_col.button("New vascular case", type="primary", use_container_width=True, key="report_new"):
        new_case()
        st.rerun()

st.divider()
st.caption(
    "VascuCase AI is a Build Week educational prototype. Clinical content is simplified and requires expert curricular review before deployment."
)
