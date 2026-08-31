# OpenAI Build Week submission checklist

## Working project

- [x] Continue development in Codex using GPT-5.6
- [x] Preserve the primary Codex Session ID: `019f76b0-8bf6-7730-a255-00ab9c632bb3`
- [x] Make meaningful timestamped commits during the submission period
- [x] Run `pytest -q` after the registration revision (`212 passed`)
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
- [ ] `SUPABASE_URL` and server-only `SUPABASE_SECRET_KEY` added to Streamlit deployment secrets
- [ ] Confirm `supabase/` is the GitHub integration working directory (`.` from repository root)
- [ ] Link the intended project, verify its reference, and inspect `supabase migration list` plus existing remote schemas before any apply
- [ ] For a verified clean/reconciled target only, review `supabase db push --dry-run`, then apply the versioned migration
- [ ] Verify new registration, exact duplicate-email reuse without profile disclosure or overwrite, and neutral handling of conflicting duplicate data against Supabase
- [ ] Verify institution fields, medical-student institutional-number requirement, `consent_version`/`consented_at`, result persistence, and overall/per-version attempt numbering
- [ ] Confirm no direct `anon`/`authenticated`/`service_role` table access and that only the intended service-role RPC wrappers execute
- [ ] `OPENAI_MODEL=gpt-5.6` configured
- [x] Fallback feedback verified

No remote migration was applied during the documented local implementation. Do not mark the migration or live Supabase checks complete until the target's history is reviewed and the hosted behavior is observed.

## Privacy and data governance

- [ ] Deployment privacy notice names the profile and result fields as identifiable operational data
- [ ] Retention, access, participant/result deletion, and incident-response procedures are approved by the operator/institution
- [ ] Downloaded reports are confirmed to exclude registration identifiers
- [ ] Any research/analytics export has an approved de-identification or pseudonymization process, access controls, and re-identification-risk review; it is not labeled anonymous by default
- [ ] Test accounts use controlled test identity data, and no real patient information is entered

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
2. Enter a controlled test name and email, training level, institution, institutional number when required, and accept the data-use notice.
3. Complete the four decision points.
4. Review the deterministic score, saved overall/per-version attempt status, and critical omissions.
5. Review personalized GPT-5.6 feedback if enabled; otherwise the app displays the rubric fallback.
6. Download the JSON performance report and confirm it excludes registration identifiers.
7. End the local session, submit the exact same normalized registration data, and confirm the app proceeds without displaying stored profile details or prior scores.
8. Submit a conflicting field for that email and confirm the app returns only a neutral check-your-information message without changing the stored row.

Use controlled test identity data only. Never enter real patient information.
