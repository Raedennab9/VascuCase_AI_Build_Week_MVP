# Devpost submission copy

## Project name

**VascuCase AI**

## Elevator pitch

An adaptive vascular-surgery case simulator that uses transparent clinical scoring and GPT-5.6 feedback to teach time-critical decision-making safely.

## Track

**Education**

## About the project

### Inspiration

Vascular emergencies require rapid recognition, structured assessment, and timely escalation. Yet learners may encounter relatively few high-risk vascular cases during training, and conventional multiple-choice questions do not reproduce the sequential reasoning required in real clinical practice.

As a vascular surgeon and medical educator, I wanted to create an interactive environment in which a learner could work through a vascular emergency step by step, commit to decisions, identify urgent priorities, and receive immediate individualized feedback. This led to **VascuCase AI**, an adaptive vascular-surgery case simulator designed for education rather than clinical decision-making.

### What it does

The MVP presents a progressive fictional case of **acute lower-limb ischaemia**. The learner chooses a training level and completes four decision points:

1. Recognize the clinical syndrome and initiate immediate actions.
2. Classify limb viability using the Rutherford system.
3. Select an investigation strategy that does not create harmful delay.
4. Plan urgent revascularization and post-reperfusion surveillance.

The application detects critical omissions and unsafe choices, generates a section-by-section score, and produces an educational performance report. The report can be downloaded as JSON.

### How it works

VascuCase AI deliberately separates clinical correctness from generative explanation.

- A **deterministic expert-authored rubric** scores diagnosis, anticoagulation, urgent vascular escalation, Rutherford classification, imaging timing, revascularization urgency, and post-reperfusion monitoring.
- **GPT-5.6** receives the validated score, learner level, and model pathway, then produces personalized formative feedback without changing the score.
- A **rubric-based fallback** preserves the complete user experience when no API key is configured, making the project easy for judges to test.

### How I built it

I used **Codex** to develop and refine the Python and Streamlit project structure, progressive session flow, clinical case schema, scoring logic, tests, documentation, and deployment workflow. GPT-5.6 is integrated through the OpenAI Responses API for constrained, learner-level feedback.

The clinical content was written as an original fictional scenario and cross-checked against the ESVS acute limb ischaemia guideline and the 2024 ESC peripheral arterial and aortic disease guideline.

> Before submission, replace this paragraph with an exact account of the Codex work completed in your primary build thread. Include your dated commits and `/feedback` Codex Session ID in the required form fields.

### Challenges

The central challenge was balancing realism with safety. A medical simulator should feel authentic, but it must not become an unrestricted diagnostic chatbot. I therefore made the scoring rubric authoritative and limited GPT-5.6 to explanation and coaching.

Another challenge was evaluating urgent management without pretending that one procedure is universally correct. The rubric accepts an immediately available open, endovascular, or hybrid strategy when it is appropriate to anatomy, cause, patient factors, and local expertise. The critical requirement is timely reperfusion.

A third challenge was ensuring testability. API access should improve the experience but should not determine whether judges can complete the project. The deterministic fallback makes the full case operational without secrets or paid services.

### What I learned

I learned that generative AI is most useful in high-stakes education when it is constrained by an explicit domain model. GPT-5.6 can personalize explanations and adapt vocabulary to learner level, while deterministic rules provide transparency, reproducibility, and protection against model drift.

I also learned how Codex can accelerate the complete development cycle: architecture, implementation, debugging, test generation, documentation, and deployment preparation.

### Accomplishments

- Built a complete stepwise vascular emergency simulation
- Implemented a transparent 100-point scoring rubric
- Added critical-omission and unsafe-choice detection
- Integrated constrained GPT-5.6 feedback
- Added a no-key fallback for reliable judging
- Added downloadable learner reports and automated tests
- Embedded guideline references and an explicit safety boundary

### What’s next

Future modules could cover carotid stenosis after TIA, ruptured abdominal aortic aneurysm, chronic limb-threatening ischaemia, venous thromboembolism, vascular trauma, and dialysis-access emergencies. Later versions could add educator-authored cases, OSCE mode, longitudinal learner analytics, and curriculum-level dashboards.

### Safety statement

VascuCase AI is intended exclusively for medical education using fictional clinical scenarios. It is not a medical device, does not provide patient-specific diagnosis or treatment recommendations, and must not be used to guide actual clinical care.

## Built with tags

- Python
- Streamlit
- OpenAI API
- GPT-5.6
- Codex
- JSON
- GitHub
- Pytest

Remove any tag that is not actually present in the submitted version.

## Try it out links

- **Live app:** `ADD_STREAMLIT_URL`
- **Source code:** `ADD_GITHUB_REPOSITORY_URL`

## Recommended gallery images

1. Landing page and learner-level selector
2. Initial fictional presentation
3. Rutherford classification decision
4. Investigation timing decision
5. Revascularization plan
6. Final performance report
7. Architecture diagram

Use 3:2 screenshots, remove browser clutter, and include no real patient data or copyrighted clinical images.
