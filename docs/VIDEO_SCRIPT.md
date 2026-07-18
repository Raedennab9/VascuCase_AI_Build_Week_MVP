# Public demo video script — target 2:40 to 2:55

## 0:00–0:18 — Problem

“Vascular emergencies are uncommon enough that many learners get limited practice, but when they occur, recognition and escalation must be immediate. VascuCase AI is a fictional, education-only vascular case simulator that teaches this time-critical reasoning.”

## 0:18–0:35 — Safety and architecture

“The project does not diagnose real patients. Clinical correctness comes from a transparent expert-authored rubric. GPT-5.6 is used only to personalize feedback after the deterministic score has been calculated.”

## 0:35–1:45 — Live case walkthrough

- Select “Surgical resident.”
- Start the acute lower-limb ischaemia case.
- Identify acute limb ischaemia.
- Select urgent vascular activation, unfractionated heparin, analgesia, IV access, fasting, and urgent labs.
- Classify the neurological deficit as Rutherford IIb.
- Choose rapid imaging only if it does not delay revascularization.
- Choose immediate revascularization and appropriate open/endovascular/hybrid components.

Narration: “The case is progressive, so later findings are not disclosed before the learner commits to the earlier decision.”

## 1:45–2:15 — Results

Show the score, strengths, critical omissions, section scoring, model pathway, GPT-5.6 feedback, and JSON download.

Narration: “Unsafe choices are explicitly flagged. With no API key, the app still produces reliable rubric-based feedback, so the complete experience remains testable.”

## 2:15–2:42 — Codex and GPT-5.6

“Codex helped build the Streamlit interface, session-state workflow, modular case schema, scoring engine, automated tests, documentation, and deployment setup. GPT-5.6 receives only the validated score and expert pathway, then adapts the explanation to the learner’s level.”

Show a brief view of the repository, tests, and one Codex session excerpt. Do not expose API keys.

## 2:42–2:55 — Close

“VascuCase AI demonstrates a safer pattern for generative AI in medical education: deterministic clinical standards, adaptive explanation, and an explicit boundary against real patient care.”
