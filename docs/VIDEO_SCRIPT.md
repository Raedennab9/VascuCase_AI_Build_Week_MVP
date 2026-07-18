# Public demo video script — target 2:40 to 2:55

## 0:00–0:16 — Problem and safety

“Vascular emergencies are time-critical, but learners may have few opportunities to practice them. VascuCase AI is an education-only simulator built from eight fictional cases. It never diagnoses real patients.”

## 0:16–0:37 — Landing and case library

Show learner level and the three case modes. Open the category selector and specific-case list, then return to random mode.

“Learners can draw a random case, choose a vascular category, or select a specific non-diagnostic case title. Random mode avoids immediate repeats and tracks completion across the eight-case library.”

## 0:37–1:32 — Progressive case walkthrough

Start “The suddenly painful, cold leg” as a surgical resident.

- Choose immediate vascular activation, heparin, analgesia, and preparation.
- Classify the neurological deficit as immediately threatened.
- Choose rapid treatment-directed imaging without reperfusion delay.
- Choose immediate open, endovascular, or hybrid revascularization with reperfusion surveillance.

“Later findings appear only after each answer is locked, and the diagnosis remains concealed. The same four-stage engine also runs limb salvage, carotid, aortic, venous, trauma, popliteal aneurysm, and mesenteric cases.”

## 1:32–2:08 — Results and report

Show the final diagnosis reveal, 100-point score, performance band, domain scores, correct actions, critical omissions, unsafe flags, expert pathway, feedback source, and JSON download.

“The score is produced only by the case rubric. The public app works offline and labels this Expert rubric-based feedback. The downloaded report contains case metadata and rubric results, never unrestricted answers or identifiers.”

Click **New vascular case**, choose “Pain out of proportion,” and briefly show its first stage to demonstrate the reusable library.

## 2:08–2:38 — Codex and GPT-5.6 architecture

Show `vascucase/cases/schema.py`, the case library, scorer, and a `107 passed` terminal result.

“Codex helped refactor the starter into validated case objects, deterministic scoring, resilient Streamlit state, safe reporting, and parametrized tests for every explicitly unsafe option. GPT-5.6 is optional and isolated downstream: it can improve explanation, but it cannot calculate or change the score, omissions, expert pathway, or diagnosis.”

## 2:38–2:55 — Close

“VascuCase AI demonstrates a safer pattern for generative AI in medical education: explicit clinical standards, adaptive explanation, complete offline operation, and a firm boundary against real patient care.”

Do not show API keys, Streamlit secrets, real patient data, or copyrighted clinical images during recording.
