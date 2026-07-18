# Validation report

Validated on July 19, 2026.

## Environment

- Python 3.11.13
- Streamlit 1.59.2
- OpenAI Python SDK 2.46.0
- Pydantic 2.13.4
- Pytest 8.4.2

## Library and deterministic scoring

- Eight unique Pydantic-validated fictional cases: passed
- Exactly four ordered stages per case: passed
- Stable, case-unique option IDs: passed
- Correct and unsafe rubric IDs resolve to declared options: passed
- Every rubric totals exactly 100 points: passed
- References and take-home learning points present in every case: passed
- Synthetic-case flags and common patient-identifier-field rejection: passed
- Expert path scores 100/100 in all eight cases: passed
- Critical omission detection in all eight cases: passed
- Every explicitly declared unsafe option is flagged: passed
- Shared bands at exact thresholds (90/75/60): passed

## Selection, state, interface, and reporting

- Random selection and no immediate repeat: passed
- Completed-case filtering and all-eligible history reset: passed
- Category filtering: passed
- Required-answer validation: passed
- Restart clears current answers and retains the current case: passed
- New-case navigation preserves completed history and returns to landing: passed
- Incomplete report state safely recovers to landing: passed
- Final diagnosis concealed before submission and revealed afterward: passed
- Complete Streamlit interaction for acute limb ischaemia: passed
- Complete Streamlit interaction for ruptured abdominal aortic aneurysm: passed
- Complete Streamlit interaction for acute mesenteric ischaemia: passed
- JSON download control does not rerun or corrupt report state: passed
- JSON includes required case/scoring metadata and excludes answers/free text: passed

## Feedback boundary

- No-key path produces case-specific “Expert rubric-based feedback”: passed
- API failure is not labeled AI-enhanced: passed
- Valid mocked GPT-5.6 response is labeled “AI-enhanced explanation”: passed
- Responses API request uses `gpt-5.6`, low reasoning, low verbosity, disabled storage, and anonymous safety identifier: passed
- Authoritative case and deterministic result remain unchanged: passed

## Build and deployment checks

- Pinned requirements installed: passed
- `pytest -q`: **107 passed in 23.16s**
- Python compilation (`compileall`): passed
- Installed-package consistency (`pip check`): passed
- Git diff whitespace/error check: passed
- Streamlit local health endpoint: **200 ok**
- High-confidence credential-pattern scan: no matches

## Accessibility and responsive implementation

- Native Streamlit form controls and semantic status components are used.
- Required controls expose visible errors.
- Keyboard focus has a high-contrast outline.
- Mobile spacing/type rules are retained.
- Reduced-motion preferences disable transitions and animation.
- Sidebar behavior remains responsive and stage content uses wrapping native containers.

## Not verified in this environment

- Live GPT-5.6 response, because no user API key was used
- Public Streamlit Community Cloud deployment and live URL
- Screenshot-based desktop/mobile browser regression: the Codex browser runtime could not connect because Windows denied access to its `AppData` runtime path (`EPERM`); Streamlit's native interaction harness covered three full cases, restart, new-case, conceal/reveal, validation, and download instead
- External clinical expert review or formal assessment-rubric validation
- Public YouTube video and final Devpost form submission

These remaining items require the project owner's credentials, public accounts, or independent clinical/curricular review.
