# Validation report

Validated on August 31, 2026.

## Environment

- Python 3.11.13
- Streamlit 1.59.2
- OpenAI Python SDK 2.46.0
- Pydantic 2.13.4
- Pytest 8.4.2
- Supabase Python client 2.31.0
- email-validator 2.3.0

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
- Single-form registration validates normalized email, full name, the exact shared training levels, normalized institution, conditional institutional number, and required consent: passed
- Institution numbers preserve text formatting, including letters, hyphens, and leading zeroes; no institution-number uniqueness is imposed: passed
- Exact duplicate registration reuses the participant UUID internally without displaying stored private data or overwriting demographics or historical consent metadata: passed
- Conflicting duplicate-email data receives a neutral failure and leaves the registration gate closed: passed
- `consent_version` is the application constant `vascucase-data-use-v1`, and `consented_at` persists: passed
- Registration and result RPC wrappers accept both a direct dictionary row (the live Supabase shape) and a compatible one-row list; invalid or ambiguous shapes are classified as non-retryable response-validation errors: passed
- Result RPC payload includes `case_version`; database response mapping validates calculated percentage, overall `attempt_number`, per-version `version_attempt_number`, and stable-result-ID retry behavior: passed
- Static migration contract covers participant/result constraints and indexes, RLS, private definer helpers with an empty search path, restricted service-role wrappers, and no institution-number uniqueness: passed
- Placeholder-only secrets example requires only `SUPABASE_URL` and `SUPABASE_SECRET_KEY`; persistence-client validation rejects a public client key in the server-secret field: passed
- Invalid or incomplete registration state clears participant-bound attempt/history state and cannot bypass the landing gate: passed

## Feedback boundary

- No-key path produces case-specific “Expert rubric-based feedback”: passed
- API failure is not labeled AI-enhanced: passed
- Valid mocked GPT-5.6 response is labeled “AI-enhanced explanation”: passed
- Responses API request uses `gpt-5.6`, low reasoning, low verbosity, disabled storage, and a random safety identifier that is not the participant ID: passed
- Authoritative case and deterministic result remain unchanged: passed

## Build and deployment checks

- Pinned requirements installed: passed
- `pytest -q`: **212 passed in 25.78s**
- Database/identity tests: **76 passed**
- Streamlit flow tests: **34 passed**
- Python compilation (`compileall`): passed
- Installed-package consistency (`pip check`): passed
- Git diff whitespace/error check: passed
- Streamlit local health endpoint: **200 ok**
- High-confidence credential-pattern scan: no matches
- Supabase CLI installed and checkout linked to project `gyuatepflreqnfocvspp`: verified
- Versioned VascuCase migration applied to the hosted Supabase database: verified
- Live registration RPC returns the supported dictionary row shape through `supabase-py`: verified
- Local Streamlit participant registration persists successfully to hosted Supabase: verified

## Accessibility and responsive implementation

- Native Streamlit form controls and semantic status components are used.
- Required controls expose visible errors.
- Keyboard focus has a high-contrast outline.
- Mobile spacing/type rules are retained.
- Reduced-motion preferences disable transitions and animation.
- Sidebar behavior remains responsive and stage content uses wrapping native containers.

## Not verified in this environment

- Live GPT-5.6 response, because no user API key was used
- Live hosted case-result insertion, retry idempotency, and concurrent overall/per-version attempt allocation
- Public Streamlit Community Cloud deployment and live URL
- Screenshot-based desktop/mobile browser regression: the Codex browser runtime could not connect because Windows denied access to its `AppData` runtime path (`EPERM`); Streamlit's native interaction harness covered three full cases, restart, new-case, conceal/reveal, validation, and download instead
- External clinical expert review or formal assessment-rubric validation
- Public YouTube video and final Devpost form submission

These remaining items require the project owner's credentials, public accounts, or independent clinical/curricular review.
