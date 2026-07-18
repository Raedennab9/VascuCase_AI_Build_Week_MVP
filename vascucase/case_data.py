from __future__ import annotations

LEARNER_LEVELS = ["Medical student", "Surgical resident", "Vascular trainee"]

CASE = {
    "id": "ali_rutherford_iib_001",
    "title": "The suddenly painful, cold right leg",
    "module": "Acute lower-limb ischaemia",
    "presentation": (
        "A 72-year-old man presents 4 hours after sudden onset of severe right calf and foot pain. "
        "The foot became cold and numb over the last hour. He has non-valvular atrial fibrillation and is not "
        "currently anticoagulated. He has no active bleeding, recent intracranial haemorrhage, or known heparin allergy. "
        "Blood pressure is 146/82 mmHg, pulse 112 beats/min and irregular, and he is afebrile."
    ),
    "examination": (
        "The right foot is pale and cool. The femoral pulse is palpable, but popliteal and pedal pulses are absent. "
        "No arterial Doppler signal is detected at the ankle; a venous Doppler signal is present. Sensory loss extends "
        "beyond the toes across the forefoot, and ankle dorsiflexion and toe movement are weak but present. The calf is soft."
    ),
    "investigation_context": (
        "The vascular team is present and an operating theatre can be available promptly. CTA can be performed immediately, "
        "but any investigation must not create a clinically important delay to reperfusion. Renal function is not yet known."
    ),
    "management_context": (
        "The pattern is compatible with an embolic occlusion in a limb without known severe chronic arterial disease. "
        "The limb has sensory loss and motor weakness. Definitive anatomy and local expertise will determine the exact open, "
        "endovascular, or hybrid technique."
    ),
    "stage1": {
        "diagnosis_options": [
            "Acute lower-limb ischaemia",
            "Chronic limb-threatening ischaemia",
            "Acute deep-vein thrombosis",
            "Peripheral neuropathy",
        ],
        "priority_options": [
            "Urgently activate the vascular team",
            "Start intravenous unfractionated heparin unless contraindicated",
            "Provide analgesia and establish intravenous access",
            "Keep the patient fasting and obtain urgent baseline blood tests/crossmatch",
            "Apply compression and elevate the limb",
            "Wait for routine outpatient vascular imaging",
        ],
    },
    "stage2": {
        "classification_options": [
            "Rutherford I — viable",
            "Rutherford IIa — marginally threatened",
            "Rutherford IIb — immediately threatened",
            "Rutherford III — irreversible",
        ],
        "decisive_options": [
            "Sensory loss extending beyond the toes",
            "Mild motor weakness",
            "Absent distal arterial Doppler signal with preserved venous signal",
            "A palpable femoral pulse",
            "Irregular tachycardia",
        ],
    },
    "stage3": {
        "investigation_options": [
            "Immediate anatomical imaging only if it does not delay urgent revascularization",
            "Routine CTA first, even if revascularization is delayed",
            "Outpatient duplex ultrasonography within one week",
            "No vascular assessment is required because the diagnosis is clinical",
        ],
        "adjunct_options": [
            "Bedside continuous-wave Doppler assessment",
            "Full blood count, coagulation profile, electrolytes, creatinine and creatine kinase",
            "ECG and later embolic-source evaluation",
            "Group and crossmatch blood",
            "Exercise ankle–brachial pressure testing",
        ],
    },
    "stage4": {
        "urgency_options": [
            "Immediate/urgent revascularization",
            "Revascularization within 1–2 weeks",
            "Anticoagulation alone with outpatient review",
            "Primary major amputation without assessing reversibility",
        ],
        "strategy_options": [
            "Urgent surgical embolectomy/thrombectomy when anatomy and expertise favour it",
            "Urgent endovascular or hybrid thrombus-removal strategy when appropriate and immediately available",
            "Treat any underlying arterial lesion identified after thrombus removal",
            "Monitor for reperfusion injury and compartment syndrome; consider fasciotomy when indicated",
            "Investigate the embolic source and plan long-term stroke/systemic embolism prevention",
            "Use systemic intravenous thrombolysis as routine therapy",
            "Delay intervention until motor weakness resolves",
        ],
    },
    "model_pathway": {
        "Recognition": (
            "This is acute limb ischaemia: abrupt pain, pallor, coldness, pulselessness, sensory disturbance, and evolving motor deficit. "
            "Immediate vascular-surgical involvement is required."
        ),
        "Initial treatment": (
            "In the absence of a contraindication, initiate intravenous unfractionated heparin, provide analgesia, establish access, "
            "keep the patient fasting, and obtain urgent laboratory tests and blood preparation in parallel."
        ),
        "Classification": (
            "Sensory loss beyond the toes plus mild motor weakness indicates Rutherford IIb acute limb ischaemia—an immediately threatened "
            "limb requiring urgent revascularization."
        ),
        "Imaging": (
            "Obtain rapid anatomical imaging when it will guide treatment without delaying reperfusion. Neurological deficit makes time to "
            "revascularization the dominant priority."
        ),
        "Revascularization": (
            "Proceed urgently with the fastest appropriate open, endovascular, or hybrid strategy based on suspected cause, anatomy, duration, "
            "comorbidity, and local expertise. Treat any underlying lesion after thrombus removal."
        ),
        "After reperfusion": (
            "Monitor closely for compartment syndrome, rhabdomyolysis, hyperkalaemia, acidosis, renal injury, recurrent ischaemia, and bleeding. "
            "Evaluate the embolic source and establish appropriate long-term antithrombotic prevention."
        ),
    },
}
