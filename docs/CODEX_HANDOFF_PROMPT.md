# Prompt to paste into Codex

Open this repository as the primary OpenAI Build Week build thread. Treat the existing files as a starter created on July 18, 2026. Use GPT-5.6 and make meaningful improvements during the submission period.

Tasks:

1. Inspect the complete repository and explain the architecture briefly.
2. Install dependencies and run `pytest -q`.
3. Launch the Streamlit app and test every stage, including restart and report download.
4. Fix any runtime, state-management, accessibility, or responsive-layout problems you find.
5. Add tests that cover every explicitly unsafe option in the scoring rubric.
6. Improve the README only where required to match the final implementation.
7. Prepare the repository for Streamlit Community Cloud deployment without exposing secrets.
8. Keep the medical scoring deterministic; do not let the language model alter the validated score or model pathway.
9. Do not add real patient data or diagnostic functionality.
10. At the end, run `/feedback` and give me the Codex Session ID required for Devpost.

Commit changes with clear, timestamped messages so the Build Week work is auditable.
