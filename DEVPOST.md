# Devpost submission copy

## Project name

**VascuCase AI**

## Elevator pitch

An eight-case vascular-surgery simulator that combines transparent deterministic scoring with optional GPT-5.6 explanation to teach high-stakes reasoning safely.

## Track

**Education**

## About the project

### Inspiration

Vascular emergencies require rapid recognition, structured assessment, and timely escalation, yet learners may encounter relatively few of them during training. Conventional multiple-choice questions also flatten the sequential reasoning of real practice. VascuCase AI provides a fictional, progressive environment where learners commit to a decision before seeing the next stage and receive immediate, reproducible feedback.

### What it does

The learner first registers a full name, normalized email address, training level, institution, institutional number when required, and explicit versioned data-use consent. Registration and result writes use a server-side Supabase client. The learner can then choose a random case, a category, or a specific case. Eight scenarios cover acute limb ischaemia, chronic limb-threatening ischaemia, symptomatic carotid disease, ruptured abdominal aortic aneurysm, thrombosed popliteal aneurysm, phlegmasia cerulea dolens, penetrating femoral vascular trauma, and acute embolic mesenteric ischaemia.

Every case has four stages: recognition, severity/anatomy, investigation and immediate management, and definitive escalation. The app conceals the diagnosis until submission, calculates a 100-point score with domain detail, identifies missed critical actions and unsafe choices, reveals the expert pathway, and downloads an identifier-free JSON report. Random mode avoids immediate repeats and resets its completed-case history after the eligible library has been completed.

### How it works

VascuCase AI separates clinical correctness from generative explanation:

- Pydantic validates each fictional case, stable option IDs, four-stage structure, references, learning points, and 100-point rubric.
- A deterministic Python engine is authoritative for the score, performance band, critical omissions, unsafe flags, expert pathway, and final diagnosis.
- Expert-authored offline feedback uses the selected correct actions, omissions, unsafe selections, case learning points, and learner level.
- The application uses a server-only Supabase secret for narrow participant/result persistence RPCs. Results retain both overall and case-version attempt numbers.
- Email ownership is not verified. An exact duplicate registration may reuse the existing participant UUID only for internal result linkage; conflicting values receive a neutral response, stored demographics are never overwritten, and prior profile data or scores are never displayed.
- Participant profiles and linked results are identifiable operational data. The downloadable report excludes registration identifiers; any research export must be intentionally de-identified or pseudonymized and must not be represented as inherently anonymous.
- When an API key is configured, GPT-5.6 receives only validated rubric-controlled data and can enhance the prose. It cannot write back to scoring state. Failed or absent calls remain explicitly labeled “Expert rubric-based feedback.”

### How I built it

I used Codex in the primary Build Week thread to audit and expand the existing Streamlit starter, design the reusable case schema and state machine, author and validate the eight-case library, isolate the OpenAI Responses API boundary, build safe report export, and add broad automated coverage. The responsive interface preserves visible keyboard focus, reduced-motion support, semantic Streamlit components, required-answer validation, restart recovery, and mobile spacing. The Supabase CLI is installed and linked, the version-controlled participant/result migration is applied to the hosted project, the live registration RPC is verified, and the local Streamlit application persists participant registration successfully.

The 212-test suite parametrizes all eight rubrics and every explicitly unsafe option, validates the registration gate, normalized-email duplicate handling, institution/consent fields, RPC response-shape compatibility, version-aware result storage, retry idempotency, selection/history behavior, and report privacy, and completes multiple cases through Streamlit’s native interaction harness. Clinical content is original and fictional, with case-specific society and consensus references linked after completion.

### Challenges

The central challenge was making eight clinically different pathways reusable without turning the interface into a diagnostic chatbot. Stable option IDs and validated case objects let the same Streamlit engine render every case while keeping clinical judgment in explicit, auditable rules.

Another challenge was procedure nuance. The rubrics reward urgency and appropriate pathway selection while allowing anatomy, physiology, local expertise, and patient factors to determine open, endovascular, or hybrid technique where guidelines support individualized care.

Randomization also needed safe state behavior: completed cases persist across new-case navigation, an immediate repeat is removed from the candidate set, and the history resets only when every eligible case is complete.

### What I learned

Generative AI is most useful in high-stakes education when it is downstream of an explicit domain model. GPT-5.6 can adapt explanation and coaching language, while deterministic rules provide transparency, repeatability, and protection against model drift. Schema validation and parametrized tests also turn clinical content into inspectable application data rather than hidden UI logic.

### Accomplishments

- Expanded one scenario into eight complete fictional vascular cases
- Added three selection modes, no-repeat randomization, and completed-case history
- Implemented Pydantic validation and eight authoritative 100-point rubrics
- Added consistent performance bands and domain-level scoring
- Implemented persistent participant registration with institution and versioned-consent metadata through restricted server-side Supabase RPCs
- Kept deterministic scoring and expert feedback operational without an OpenAI secret; Supabase remains required for registration and result persistence
- Isolated optional GPT-5.6 explanation from all clinical scoring state
- Added diagnosis conceal/reveal, restart/new-case recovery, and safe JSON reports
- Reached 212 passing automated tests, including every declared unsafe choice and the persistent registration/result flow

### What’s next

Next steps include external vascular-education review, formal rubric validation, production backup/monitoring procedures, live result-write and concurrency verification, a stronger verified-identity design before any learner-history feature, educator-authored case tooling, governed de-identified or pseudonymized analytics, localization, and accessibility testing with additional assistive technologies. The application will remain a fictional educational simulator rather than a diagnostic product.

### Safety statement

VascuCase AI is intended exclusively for medical education using fictional clinical scenarios. It is not a medical device, does not provide patient-specific diagnosis or treatment recommendations, and must not be used to guide actual clinical care.

## Built with tags

- Python
- Streamlit
- Pydantic
- OpenAI API
- GPT-5.6
- Codex
- JSON
- GitHub
- Supabase
- Pytest

## Try it out links

- **Live app:** `ADD_STREAMLIT_URL`
- **Source code:** [github.com/Raedennab9/VascuCase_AI_Build_Week_MVP](https://github.com/Raedennab9/VascuCase_AI_Build_Week_MVP)
- **Codex Session ID:** `019f76b0-8bf6-7730-a255-00ab9c632bb3`

## Recommended gallery images

1. Participant registration landing and the three case modes
2. Case category/difficulty badges and progressive decision stage
3. A second case to demonstrate the reusable engine
4. Final diagnosis reveal and domain scores
5. Expert feedback source label and JSON download
6. Architecture diagram and green test run

Use 3:2 screenshots, remove browser clutter, and include no real patient data, API keys, or copyrighted clinical images.
