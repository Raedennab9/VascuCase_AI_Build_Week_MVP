from __future__ import annotations

import secrets

import streamlit as st

from vascucase.case_data import CASE, LEARNER_LEVELS
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
  --vc-cream: #f7f5f0;
}
.block-container {max-width: 1120px; padding-top: 1.4rem;}
.vc-hero {
  background: linear-gradient(120deg, var(--vc-navy), var(--vc-blue));
  color: white; padding: 1.6rem 1.8rem; border-radius: 18px;
  margin-bottom: 1rem;
}
.vc-kicker {letter-spacing: .09em; text-transform: uppercase; font-size: .78rem; opacity: .82;}
.vc-reference {font-size: .88rem; color: #475569;}
.small-note {font-size: .85rem; color: #64748b;}
*:focus-visible {outline: 3px solid #f59e0b !important; outline-offset: 3px;}
@media (max-width: 700px) {
  .block-container {padding: .8rem 1rem 2rem;}
  .vc-hero {padding: 1.1rem 1.15rem; border-radius: 13px;}
  .vc-hero h1 {font-size: 2rem !important;}
  .vc-hero p {font-size: 1rem !important;}
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {scroll-behavior: auto !important; transition: none !important;}
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def init_state() -> None:
    defaults = {
        "stage": 0,
        "answers": {},
        "result": None,
        "feedback": None,
        "learner_level": LEARNER_LEVELS[1],
        "safety_identifier": secrets.token_hex(16),
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    if not isinstance(st.session_state.answers, dict):
        st.session_state.answers = {}
    if st.session_state.stage not in range(6):
        st.session_state.stage = 0
        st.session_state.result = None
        st.session_state.feedback = None
    if st.session_state.stage == 5 and (
        not isinstance(st.session_state.result, dict)
        or not isinstance(st.session_state.feedback, dict)
    ):
        st.session_state.stage = 0
        st.session_state.answers = {}
        st.session_state.result = None
        st.session_state.feedback = None


def reset_case() -> None:
    for key in ["stage", "answers", "result", "feedback"]:
        if key in st.session_state:
            del st.session_state[key]
    init_state()


def save_answer(section: str, payload: dict) -> None:
    st.session_state.answers[section] = payload


init_state()

with st.sidebar:
    st.title("VascuCase AI")
    st.caption("Adaptive vascular-surgery case simulation")
    st.selectbox(
        "Learner level",
        LEARNER_LEVELS,
        key="learner_level",
        disabled=st.session_state.stage > 0,
    )
    completed = max(0, st.session_state.stage - 1)
    st.progress(min(completed / 4, 1.0), text=f"Case progress: {min(completed, 4)}/4")
    st.divider()
    st.markdown("**Current module**")
    st.write(CASE["title"])
    st.caption(CASE["module"])
    if st.button("Restart case", use_container_width=True):
        reset_case()
        st.rerun()
    st.divider()
    st.warning(
        "**Education only.** Fictional scenario. Not a diagnostic or treatment tool "
        "and not for real-time patient care."
    )

st.markdown(
    """
    <div class="vc-hero">
      <div class="vc-kicker">OpenAI Build Week prototype</div>
      <h1 style="margin:.25rem 0 .45rem 0;">VascuCase AI</h1>
      <p style="margin:0; font-size:1.08rem;">Practice time-critical vascular reasoning through a progressive, rubric-grounded clinical simulation.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("Fictional educational case. Do not enter real patient information.")

if st.session_state.stage == 0:
    left, right = st.columns([1.45, 1])
    with left:
        st.subheader("Acute lower-limb ischaemia")
        st.write(
            "You will assess a fictional patient through four decision points: initial recognition, "
            "limb-viability classification, investigation strategy, and definitive management."
        )
        st.markdown(
            """
            **What is assessed**
            - Recognition of a vascular emergency
            - Rutherford limb-viability classification
            - Time-sensitive anticoagulation and escalation
            - Imaging without harmful delay
            - Urgent revascularization planning and post-reperfusion surveillance
            """
        )
        st.info("The scoring engine uses explicit expert-authored rules. GPT-5.6 is used only to personalize the educational explanation.")
        if st.button("Start simulation", type="primary", use_container_width=True):
            st.session_state.stage = 1
            st.rerun()
    with right:
        with st.container(border=True):
            st.metric("Estimated completion", "5–7 min")
            st.metric("Decision points", "4")
            st.metric("Maximum score", "100")
            st.markdown("**Case status:** Fictional, de-identified by design")

elif st.session_state.stage == 1:
    st.subheader("Decision 1 — Initial recognition and immediate priorities")
    with st.container(border=True):
        st.write(CASE["presentation"])
    with st.form("stage1"):
        diagnosis = st.radio(
            "Most likely clinical syndrome",
            CASE["stage1"]["diagnosis_options"],
            index=None,
        )
        priorities = st.multiselect(
            "Select the immediate priorities",
            CASE["stage1"]["priority_options"],
        )
        reasoning = st.text_area(
            "Briefly explain your reasoning",
            placeholder="Identify the emergency, urgency, and first actions...",
            height=120,
            help="Use only the fictional facts shown in the simulation. Do not enter patient information.",
        )
        submitted = st.form_submit_button("Lock answer and reveal examination", type="primary")
    if submitted:
        if diagnosis is None:
            st.error("Choose the most likely clinical syndrome before continuing.")
        else:
            save_answer("stage1", {"diagnosis": diagnosis, "priorities": priorities, "reasoning": reasoning})
            st.session_state.stage = 2
            st.rerun()

elif st.session_state.stage == 2:
    st.subheader("Decision 2 — Limb viability")
    with st.container(border=True):
        st.write(CASE["examination"])
    with st.form("stage2"):
        classification = st.radio(
            "Rutherford acute limb ischaemia category",
            CASE["stage2"]["classification_options"],
            index=None,
        )
        decisive = st.multiselect(
            "Which findings determine urgency?",
            CASE["stage2"]["decisive_options"],
        )
        rationale = st.text_area("Classification rationale", height=100)
        submitted = st.form_submit_button("Lock answer and plan investigations", type="primary")
    if submitted:
        if classification is None:
            st.error("Choose a Rutherford category before continuing.")
        else:
            save_answer(
                "stage2",
                {"classification": classification, "decisive": decisive, "rationale": rationale},
            )
            st.session_state.stage = 3
            st.rerun()

elif st.session_state.stage == 3:
    st.subheader("Decision 3 — Investigation strategy")
    with st.container(border=True):
        st.write(CASE["investigation_context"])
    with st.form("stage3"):
        investigation = st.radio(
            "Best next investigation strategy",
            CASE["stage3"]["investigation_options"],
            index=None,
        )
        adjuncts = st.multiselect(
            "Select useful parallel investigations that should not delay reperfusion",
            CASE["stage3"]["adjunct_options"],
        )
        submitted = st.form_submit_button("Lock answer and choose management", type="primary")
    if submitted:
        if investigation is None:
            st.error("Choose an investigation strategy before continuing.")
        else:
            save_answer("stage3", {"investigation": investigation, "adjuncts": adjuncts})
            st.session_state.stage = 4
            st.rerun()

elif st.session_state.stage == 4:
    st.subheader("Decision 4 — Revascularization and surveillance")
    with st.container(border=True):
        st.write(CASE["management_context"])
    with st.form("stage4"):
        urgency = st.radio(
            "Required treatment urgency",
            CASE["stage4"]["urgency_options"],
            index=None,
        )
        strategies = st.multiselect(
            "Select reasonable components of the management plan",
            CASE["stage4"]["strategy_options"],
        )
        plan = st.text_area(
            "Your concise management plan",
            placeholder="State the immediate procedure, alternatives, and post-reperfusion priorities...",
            height=130,
            help="Use only the fictional facts shown in the simulation. Do not enter patient information.",
        )
        submitted = st.form_submit_button("Submit case for scoring", type="primary")
    if submitted:
        if urgency is None:
            st.error("Choose the required treatment urgency before submitting the case.")
        else:
            save_answer("stage4", {"urgency": urgency, "strategies": strategies, "plan": plan})
            result = score_case(st.session_state.answers)
            st.session_state.result = result
            with st.spinner("Preparing your educational feedback..."):
                st.session_state.feedback = generate_feedback(
                    case=CASE,
                    answers=st.session_state.answers,
                    result=result,
                    learner_level=st.session_state.learner_level,
                    safety_identifier=st.session_state.safety_identifier,
                )
            st.session_state.stage = 5
            st.rerun()

elif st.session_state.stage == 5:
    result = st.session_state.result
    feedback = st.session_state.feedback
    st.subheader("Performance report")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total score", f"{result['score']}/{result['max_score']}")
    c2.metric("Performance band", result["band"])
    c3.metric("Critical omissions", len(result["critical_misses"]))

    st.progress(result["score"] / result["max_score"])

    left, right = st.columns(2)
    with left:
        st.markdown("### Strengths")
        if result["strengths"]:
            for item in result["strengths"]:
                st.success(item)
        else:
            st.info("No scored strength was recorded. Review the model pathway below.")
    with right:
        st.markdown("### Priority corrections")
        if result["critical_misses"]:
            for item in result["critical_misses"]:
                st.error(item)
        else:
            st.success("No critical action was missed.")
        for item in result["improvements"]:
            st.warning(item)

    st.markdown("### Personalized educational feedback")
    st.info(
        "The score and expert pathway are produced only by deterministic rules. "
        "Generated feedback cannot change either one."
    )
    st.write(feedback["text"])
    st.caption(f"Feedback mode: {feedback['mode']}")

    with st.expander("Model expert pathway", expanded=True):
        for heading, text in CASE["model_pathway"].items():
            st.markdown(f"**{heading}**")
            st.write(text)

    with st.expander("Section scoring"):
        for section, data in result["sections"].items():
            st.write(f"**{section}:** {data['score']}/{data['max_score']}")
            st.caption(data["note"])

    report_json = build_report_json(
        case_title=CASE["title"],
        learner_level=st.session_state.learner_level,
        answers=st.session_state.answers,
        result=result,
        feedback=feedback,
    )
    st.download_button(
        "Download performance report (JSON)",
        data=report_json,
        file_name="vascucase_performance_report.json",
        mime="application/json",
        help="Downloads this fictional simulation attempt to your device.",
        on_click="ignore",
        use_container_width=True,
    )

    st.markdown("### Evidence base")
    st.markdown(
        "- Björck M, et al. ESVS 2020 Clinical Practice Guidelines on the Management of Acute Limb Ischaemia. "
        "*Eur J Vasc Endovasc Surg.* 2020;59:173–218. "
        "[doi:10.1016/j.ejvs.2019.09.006](https://doi.org/10.1016/j.ejvs.2019.09.006)\n"
        "- Mazzolai L, et al. 2024 ESC Guidelines for the management of peripheral arterial and aortic diseases. "
        "*Eur Heart J.* 2024;45:3538–3700. "
        "[doi:10.1093/eurheartj/ehae179](https://doi.org/10.1093/eurheartj/ehae179)"
    )

    if st.button("Try again", use_container_width=True):
        reset_case()
        st.rerun()

st.divider()
st.caption(
    "VascuCase AI is a Build Week educational prototype. Clinical content is simplified "
    "for simulation and requires expert review before curricular deployment."
)
