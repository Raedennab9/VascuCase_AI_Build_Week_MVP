# Public demo video script — target 2:40 to 2:55

## 0:00–0:16 — Problem and safety

“Vascular emergencies are time-critical, but learners may have few opportunities to practice them. VascuCase AI is an education-only simulator built from eight fictional cases. It never diagnoses real patients.”

## 0:16–0:37 — Landing and case library

Show the registration form without displaying real identity data, then use a prepared test registration to show the three case modes. Briefly show training level, institution, versioned consent, and the medical-student institutional-number rule before opening the category selector and specific-case list.

“Participants record a name, normalized email, training level, institution, and versioned consent before they can draw a random case, choose a vascular category, or select a specific non-diagnostic case title. Restricted server-side Supabase RPCs persist registration and results without exposing the database secret to the browser.”

## 0:37–1:32 — Progressive case walkthrough

Start “The suddenly painful, cold leg” as a surgical resident.

- Choose immediate vascular activation, heparin, analgesia, and preparation.
- Classify the neurological deficit as immediately threatened.
- Choose rapid treatment-directed imaging without reperfusion delay.
- Choose immediate open, endovascular, or hybrid revascularization with reperfusion surveillance.

“Later findings appear only after each answer is locked, and the diagnosis remains concealed. The same four-stage engine also runs limb salvage, carotid, aortic, venous, trauma, popliteal aneurysm, and mesenteric cases.”

## 1:32–2:08 — Results and report

Show the final diagnosis reveal, 100-point score, performance band, domain scores, correct actions, critical omissions, unsafe flags, expert pathway, feedback source, and JSON download.

“The score is produced only by the case rubric, and expert rubric-based feedback does not require an OpenAI key. Identifiable participant and performance records are stored through restricted server-side Supabase RPCs with case-version and attempt metadata. The downloaded report contains case and rubric results, never registration identifiers or unrestricted answers.”

Click **New vascular case**, choose “Pain out of proportion,” and briefly show its first stage to demonstrate the reusable library.

## 2:08–2:38 — Codex and GPT-5.6 architecture

Show `vascucase/database.py`, the case schema/library, Supabase migration, scorer, and the final passing test result. Mention that the CLI-linked migration is applied to hosted Supabase, the live registration RPC returns the supported dictionary row shape, and local Streamlit registration persistence has been verified.

“Codex helped refactor the starter into validated case objects, deterministic scoring, resilient Streamlit state, safe reporting, and parametrized tests for every explicitly unsafe option. GPT-5.6 is optional and isolated downstream: it can improve explanation, but it cannot calculate or change the score, omissions, expert pathway, or diagnosis.”

## 2:38–2:55 — Close

“VascuCase AI demonstrates a safer pattern for generative AI in medical education: explicit clinical standards, deterministic scoring, privacy-aware hosted persistence, adaptive explanation, and a firm boundary against real patient care.”

Do not show API keys, Streamlit secrets, a real email address, participant records, real patient data, or copyrighted clinical images during recording. If discussing research exports, call them de-identified or pseudonymized as applicable—not anonymous by default.
