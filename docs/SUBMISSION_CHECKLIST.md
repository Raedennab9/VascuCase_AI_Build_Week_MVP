# OpenAI Build Week submission checklist

## Working project

- [x] Continue development in Codex using GPT-5.6
- [x] Preserve the primary Codex Session ID: `019f76b0-8bf6-7730-a255-00ab9c632bb3`
- [x] Make meaningful timestamped commits during the submission period
- [x] Run `pytest -q` (`32 passed`)
- [x] Test the full case with no API key
- [ ] Test GPT-5.6 feedback with the deployment secret configured
- [ ] Confirm the app works in a private/incognito browser window
- [x] Confirm no API key or private data is committed

## Repository

- [ ] Public GitHub repository with MIT license, or private repository shared with `testing@devpost.com` and `build-week-event@openai.com`
- [x] README contains installation and testing instructions
- [x] Repository contains no real patient data
- [ ] GitHub “About” description and topics completed

Suggested repository description:

> Adaptive vascular-surgery case simulation with deterministic clinical scoring and constrained GPT-5.6 feedback.

Suggested topics:

`medical-education`, `vascular-surgery`, `streamlit`, `openai`, `gpt-5-6`, `codex`, `clinical-simulation`

## Deployment

- [ ] Public Streamlit URL added to Devpost
- [ ] `OPENAI_API_KEY` stored only as a deployment secret
- [ ] `OPENAI_MODEL=gpt-5.6` configured
- [x] Fallback feedback verified

## Devpost

- [ ] Project name: VascuCase AI
- [ ] Track: Education
- [ ] Elevator pitch entered
- [ ] Project story reviewed and updated to match the final app exactly
- [ ] Built-with tags include only technologies actually used
- [ ] Live app URL added
- [ ] Repository URL added
- [ ] 3:2 screenshots uploaded
- [ ] Public YouTube video is under 3 minutes
- [ ] Video has clear audio and explains both Codex and GPT-5.6 use
- [ ] No unlicensed music, patient images, or third-party copyrighted material
- [x] `/feedback` Codex Session ID recorded for entry: `019f76b0-8bf6-7730-a255-00ab9c632bb3`
- [ ] English testing instructions included

## Final test instructions for judges

1. Open the live application.
2. Select any learner level.
3. Complete the four decision points.
4. Review the deterministic score and critical omissions.
5. Review personalized GPT-5.6 feedback if enabled; otherwise the app displays the rubric fallback.
6. Download the JSON performance report.

No account or sample data is required.
