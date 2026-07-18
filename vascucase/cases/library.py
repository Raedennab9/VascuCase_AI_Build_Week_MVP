from __future__ import annotations

import random
from collections.abc import Sequence

from vascucase.cases.schema import (
    AnswerOption,
    CaseStage,
    Question,
    Reference,
    UnsafeChoice,
    VascularCase,
)


LEARNER_LEVELS = ("Medical student", "Surgical resident", "Vascular trainee")
CASE_MODES = ("Random vascular case", "Choose category", "Choose a specific case")
DISCLAIMER = (
    "Fictional educational simulation only. Not a diagnostic or treatment tool and not for real-time patient care."
)


def _stage(
    number: int,
    title: str,
    domain: str,
    content: str,
    prompt: str,
    options: Sequence[tuple[str, str]],
) -> CaseStage:
    return CaseStage(
        stage_id=f"stage{number}",
        title=title,
        domain=domain,
        content=content,
        question=Question(
            question_id=f"stage{number}_decision",
            prompt=prompt,
            kind="single",
            options=tuple(AnswerOption(option_id=option_id, label=label) for option_id, label in options),
        ),
    )


def _reference(citation: str, url: str) -> Reference:
    return Reference(citation=citation, url=url)


def _case(
    *,
    case_id: str,
    title: str,
    category: str,
    difficulty: str,
    presentation: str,
    stages: Sequence[CaseStage],
    correct: Sequence[str],
    critical: Sequence[str],
    unsafe: dict[str, tuple[int, str]],
    criteria: Sequence[str],
    pathway: Sequence[str],
    diagnosis: str,
    learning: Sequence[str],
    references: Sequence[Reference],
) -> VascularCase:
    weights = {option_id: 25 for option_id in correct}
    unsafe_models = {
        option_id: UnsafeChoice(penalty=penalty, explanation=explanation)
        for option_id, (penalty, explanation) in unsafe.items()
    }
    labels = {
        option.option_id: option.label
        for stage in stages
        for option in stage.question.options
    }
    explanations = {
        option_id: f"Expected pathway: {labels[option_id]}"
        for option_id in correct
    }
    explanations.update(
        {option_id: rule.explanation for option_id, rule in unsafe_models.items()}
    )
    return VascularCase(
        case_id=case_id,
        title=title,
        category=category,
        difficulty=difficulty,
        brief_presentation=presentation,
        stages=tuple(stages),
        correct_actions=tuple(correct),
        critical_actions=tuple(critical),
        unsafe_choices=unsafe_models,
        scoring_weights=weights,
        classification_criteria=tuple(criteria),
        explanations=explanations,
        model_pathway=tuple(pathway),
        final_diagnosis=diagnosis,
        learning_points=tuple(learning),
        references=tuple(references),
        educational_disclaimer=DISCLAIMER,
    )


ALI_CASE = _case(
    case_id="ali_af_embolism_iib",
    title="The suddenly painful, cold leg",
    category="Arterial emergencies",
    difficulty="Intermediate",
    presentation=(
        "A 72-year-old man has four hours of sudden severe right calf and foot pain, followed by coldness and numbness. "
        "He has atrial fibrillation and is not anticoagulated. There is no active bleeding, recent intracranial "
        "haemorrhage, or known heparin allergy. His pulse is 112 beats/min and irregular."
    ),
    stages=(
        _stage(
            1,
            "Initial recognition and focused assessment",
            "Recognition and first actions",
            "The right foot is pale and cool. The femoral pulse is present, distal pulses are absent, and symptoms began abruptly.",
            "Which immediate pathway is most appropriate?",
            (
                ("ali_s1_urgent_bundle", "Activate the vascular team, give IV unfractionated heparin unless contraindicated, provide analgesia, and prepare for urgent intervention."),
                ("ali_s1_compress", "Apply compression, elevate the leg, and reassess after analgesia."),
                ("ali_s1_outpatient", "Arrange outpatient arterial duplex within one week."),
                ("ali_s1_neuropathy", "Treat presumed neuropathic pain and review the response."),
            ),
        ),
        _stage(
            2,
            "Severity and limb viability",
            "Severity classification",
            "There is sensory loss beyond the toes, mild ankle and toe weakness, no distal arterial Doppler signal, and a preserved venous signal.",
            "How should the limb be classified?",
            (
                ("ali_s2_iib", "Immediately threatened: neurological deficit requires immediate revascularization."),
                ("ali_s2_i", "Viable: no immediate threat to the limb."),
                ("ali_s2_iia", "Marginally threatened: salvageable if treated promptly, without motor deficit."),
                ("ali_s2_iii", "Irreversible: primary major amputation without a salvage attempt."),
            ),
        ),
        _stage(
            3,
            "Investigations and immediate management",
            "Investigation strategy",
            "A vascular team and theatre are available. CTA is immediately accessible, but neurological deficit makes time to reperfusion critical.",
            "Choose the safest investigation strategy.",
            (
                ("ali_s3_rapid_imaging", "Use rapid anatomical imaging only if it will guide treatment without delaying reperfusion; obtain labs, ECG, Doppler, and crossmatch in parallel."),
                ("ali_s3_delayed_cta", "Complete routine CTA and renal optimization before calling the operating team, even if this delays reperfusion."),
                ("ali_s3_exercise_abi", "Perform exercise ankle–brachial pressure testing before vascular review."),
                ("ali_s3_no_assessment", "Proceed without any vascular assessment or treatment planning."),
            ),
        ),
        _stage(
            4,
            "Definitive management and escalation",
            "Revascularization and surveillance",
            "The pattern suggests an embolic occlusion in a limb without known severe chronic arterial disease. Anatomy and local expertise will determine technique.",
            "Which definitive plan best protects the limb?",
            (
                ("ali_s4_revascularize", "Proceed immediately with the fastest appropriate open, endovascular, or hybrid revascularization and monitor for compartment and metabolic reperfusion injury."),
                ("ali_s4_heparin_only", "Continue heparin alone and review motor function the next morning."),
                ("ali_s4_systemic_lysis", "Use routine systemic intravenous thrombolysis and defer local intervention."),
                ("ali_s4_wait_weakness", "Wait for motor weakness to resolve before deciding on intervention."),
            ),
        ),
    ),
    correct=("ali_s1_urgent_bundle", "ali_s2_iib", "ali_s3_rapid_imaging", "ali_s4_revascularize"),
    critical=("ali_s1_urgent_bundle", "ali_s2_iib", "ali_s4_revascularize"),
    unsafe={
        "ali_s1_compress": (8, "Compression and delay do not treat an acutely ischaemic arterial limb."),
        "ali_s1_outpatient": (15, "A threatened limb must not be deferred to outpatient imaging."),
        "ali_s2_iii": (15, "Motor weakness with preserved movement is not evidence of irreversible ischaemia; premature amputation abandons salvage."),
        "ali_s3_delayed_cta": (15, "Imaging must not create harmful delay when neurological deficit is present."),
        "ali_s3_exercise_abi": (8, "Exercise ABI is inappropriate in this time-critical presentation."),
        "ali_s4_heparin_only": (15, "Anticoagulation alone is insufficient for an immediately threatened limb."),
        "ali_s4_systemic_lysis": (12, "Routine systemic intravenous thrombolysis is not the definitive ALI pathway."),
        "ali_s4_wait_weakness": (15, "Motor weakness increases urgency and is not a reason to wait."),
    },
    criteria=(
        "Rutherford IIb: sensory loss beyond the toes with mild-to-moderate motor deficit and absent arterial Doppler signals.",
    ),
    pathway=(
        "Recognize abrupt arterial ischaemia and involve the vascular team immediately.",
        "Give unfractionated heparin unless contraindicated and prepare in parallel.",
        "Use neurological deficit to classify the limb as immediately threatened.",
        "Revascularize without harmful imaging delay, then monitor reperfusion and investigate the embolic source.",
    ),
    diagnosis="Atrial-fibrillation-related embolic acute lower-limb ischaemia, Rutherford IIb.",
    learning=(
        "Motor deficit in acute limb ischaemia signals an immediately threatened limb.",
        "Imaging should guide the fastest suitable revascularization, not delay it.",
        "Post-reperfusion compartment and metabolic complications require active surveillance.",
    ),
    references=(
        _reference("ESVS 2020 Clinical Practice Guidelines on Acute Limb Ischaemia", "https://esvs.org/wp-content/uploads/2021/08/Acute-Limb-Ischaemia-Feb-2020.pdf"),
    ),
)


CLTI_CASE = _case(
    case_id="clti_diabetic_gangrene_infection",
    title="The non-healing infected toe",
    category="Limb salvage",
    difficulty="Advanced",
    presentation=(
        "A 68-year-old woman with diabetes, chronic kidney disease, and smoking history has six weeks of forefoot rest pain. "
        "Her great toe is now black, with surrounding erythema, purulent drainage, and increasing pain. She is febrile at 38.2°C."
    ),
    stages=(
        _stage(
            1,
            "Initial recognition and focused assessment",
            "Recognition and infection control",
            "The foot is cool with no palpable pedal pulse. Erythema extends four centimetres from the toe wound; the patient is alert and haemodynamically stable.",
            "What is the best initial pathway?",
            (
                ("clti_s1_team", "Admit, assess sepsis and perfusion, start appropriate antibiotics, offload, and involve vascular and diabetic-foot teams urgently."),
                ("clti_s1_antibiotics_only", "Give oral antibiotics and wait for infection to resolve before vascular assessment."),
                ("clti_s1_compress", "Apply high-pressure compression to improve tissue perfusion."),
                ("clti_s1_outpatient", "Arrange routine podiatry review in six weeks."),
            ),
        ),
        _stage(
            2,
            "Severity and limb-threat staging",
            "WIfI interpretation",
            "The wound involves gangrene of the great toe; toe pressure is 24 mmHg. Cellulitis is deeper than skin and extends beyond two centimetres, without systemic shock.",
            "Which WIfI interpretation best represents these findings?",
            (
                ("clti_s2_wifi", "Wound 2, Ischaemia 3, foot Infection 2: advanced limb threat requiring prompt integrated treatment."),
                ("clti_s2_low_risk", "Minimal limb threat because only one toe is involved."),
                ("clti_s2_infection_only", "Infection severity alone determines the revascularization need."),
                ("clti_s2_no_ischaemia", "Toe pressure below 30 mmHg excludes significant ischaemia."),
            ),
        ),
        _stage(
            3,
            "Investigations and immediate management",
            "Anatomy and source control",
            "Plain radiography shows no gas. The patient remains stable after initial fluids and antibiotics; urgent limb-salvage resources are available.",
            "Which investigation and immediate-management bundle is most appropriate?",
            (
                ("clti_s3_workup", "Obtain urgent arterial imaging for revascularization planning, deep tissue culture at debridement, labs, and targeted imaging if osteomyelitis remains uncertain; drain urgent collections."),
                ("clti_s3_delay_perfusion", "Treat infection to completion before measuring perfusion or imaging arteries."),
                ("clti_s3_superficial_swab", "Use a superficial swab as the sole microbiological assessment and omit perfusion imaging."),
                ("clti_s3_mri_delay", "Delay source control and vascular planning until elective MRI is completed."),
            ),
        ),
        _stage(
            4,
            "Definitive management and escalation",
            "Limb-salvage strategy",
            "Imaging shows multilevel occlusive disease with a usable distal target. Infection remains localized to the forefoot and the patient can tolerate revascularization.",
            "What is the best definitive strategy?",
            (
                ("clti_s4_salvage", "Coordinate evidence-based revascularization with drainage/debridement or limited amputation, wound care, offloading, and cardiovascular risk reduction."),
                ("clti_s4_major_amp", "Proceed directly to major amputation without assessing a feasible limb-salvage pathway."),
                ("clti_s4_antibiotics", "Use prolonged antibiotics alone despite severe ischaemia and tissue loss."),
                ("clti_s4_revascularize_late", "Schedule revascularization only after the wound has completely healed."),
            ),
        ),
    ),
    correct=("clti_s1_team", "clti_s2_wifi", "clti_s3_workup", "clti_s4_salvage"),
    critical=("clti_s1_team", "clti_s2_wifi", "clti_s3_workup", "clti_s4_salvage"),
    unsafe={
        "clti_s1_antibiotics_only": (12, "Infection treatment must not postpone urgent perfusion assessment in a threatened limb."),
        "clti_s1_compress": (10, "High-pressure compression is unsafe in severe arterial insufficiency."),
        "clti_s1_outpatient": (15, "Gangrene with infection and severe ischaemia requires urgent multidisciplinary care."),
        "clti_s2_no_ischaemia": (10, "A toe pressure below 30 mmHg represents severe ischaemia, not its absence."),
        "clti_s3_delay_perfusion": (15, "Delaying perfusion assessment risks progression of tissue loss and infection."),
        "clti_s3_mri_delay": (10, "Necessary source control and vascular planning should not wait for elective imaging."),
        "clti_s4_major_amp": (15, "Primary major amputation is inappropriate before assessing feasible salvage in this stable patient."),
        "clti_s4_antibiotics": (12, "Antibiotics cannot correct severe ischaemia or remove necrotic tissue."),
    },
    criteria=(
        "SVS WIfI grades wound extent, objective ischaemia, and foot-infection severity to stage limb threat.",
        "Toe pressure below 30 mmHg is severe (grade 3) ischaemia in the WIfI framework.",
    ),
    pathway=(
        "Recognize combined tissue loss, infection, and severe perfusion failure.",
        "Stage wound, ischaemia, and infection rather than using one feature alone.",
        "Treat infection and define revascularization anatomy in parallel.",
        "Coordinate revascularization, source control, wound care, and secondary prevention.",
    ),
    diagnosis="Chronic limb-threatening ischaemia with diabetic great-toe gangrene and moderate foot infection.",
    learning=(
        "WIfI separates wound, ischaemia, and infection so each threat is treated explicitly.",
        "Infected tissue loss requires parallel infection control and urgent perfusion planning.",
        "Major amputation should not replace a feasible, patient-centred limb-salvage assessment.",
    ),
    references=(
        _reference("Global Vascular Guidelines on chronic limb-threatening ischemia", "https://vascular.org/research-quality/guidelines-and-reporting-standards/clinical-practice-guidelines"),
        _reference("IWGDF/IDSA 2023 guideline on diabetes-related foot infections", "https://www.idsociety.org/practice-guideline/diabetic-foot-infections/"),
    ),
)


CAROTID_CASE = _case(
    case_id="symptomatic_carotid_tia",
    title="The brief weakness that resolved",
    category="Cerebrovascular disease",
    difficulty="Intermediate",
    presentation=(
        "A 69-year-old man had 20 minutes of right-hand weakness and expressive language difficulty four days ago. "
        "Symptoms fully resolved. Duplex now suggests an 80% left internal carotid narrowing by NASCET criteria."
    ),
    stages=(
        _stage(
            1,
            "Initial recognition and focused assessment",
            "Recognition and stroke prevention",
            "Neurological examination is now normal. There is no intracranial haemorrhage on initial brain imaging and no ongoing disabling deficit.",
            "What is the best immediate pathway?",
            (
                ("car_s1_urgent", "Treat as a recent ipsilateral transient cerebral ischaemic event: urgent stroke/vascular review and optimized antiplatelet, statin, and risk-factor therapy."),
                ("car_s1_reassure", "Reassure because symptoms resolved and repeat duplex in one year."),
                ("car_s1_thrombolysis", "Give intravenous thrombolysis four days after the resolved episode."),
                ("car_s1_no_medical", "Withhold preventive medication until a procedure is chosen."),
            ),
        ),
        _stage(
            2,
            "Severity and anatomical interpretation",
            "Stenosis confirmation",
            "The symptoms localize to the left carotid territory. The patient is functionally independent and has no large established infarct.",
            "How should the vascular finding be interpreted and confirmed?",
            (
                ("car_s2_severe", "Confirm severe symptomatic ipsilateral stenosis with high-quality CTA or MRA and multidisciplinary review."),
                ("car_s2_asymptomatic", "Classify the lesion as asymptomatic because the examination is now normal."),
                ("car_s2_contralateral", "Attribute right-hand weakness to the right carotid artery."),
                ("car_s2_duplex_only", "Proceed to intervention without confirming anatomy or brain imaging."),
            ),
        ),
        _stage(
            3,
            "Investigations and immediate management",
            "Periprocedural planning",
            "CTA confirms an accessible 78% left internal carotid stenosis. There is a small non-disabling infarct and no haemorrhage; surgical risk is acceptable.",
            "Which preparation is most appropriate?",
            (
                ("car_s3_prepare", "Continue optimized medical therapy, assess operative risk and anatomy promptly, and schedule early carotid endarterectomy with stroke-team coordination."),
                ("car_s3_delay_months", "Delay any revascularization decision for three months to ensure symptom stability."),
                ("car_s3_stop_antiplatelet", "Stop all antiplatelet therapy immediately and leave the patient untreated while waiting."),
                ("car_s3_routine_stent", "Choose carotid stenting routinely without considering age, anatomy, or procedural risk."),
            ),
        ),
        _stage(
            4,
            "Definitive management and escalation",
            "Early revascularization",
            "The lesion remains surgically accessible and there is no major disability, large infarct, or medical instability that would require deferral.",
            "What is the preferred definitive strategy?",
            (
                ("car_s4_cea", "Perform carotid endarterectomy as soon as safely possible, preferably within 14 days of symptoms, with audited perioperative outcomes."),
                ("car_s4_observe", "Use observation alone despite severe recent symptomatic stenosis."),
                ("car_s4_late", "Wait at least six months before considering intervention."),
                ("car_s4_cas_all", "Use carotid stenting in every patient regardless of age, anatomy, or local outcomes."),
            ),
        ),
    ),
    correct=("car_s1_urgent", "car_s2_severe", "car_s3_prepare", "car_s4_cea"),
    critical=("car_s1_urgent", "car_s2_severe", "car_s4_cea"),
    unsafe={
        "car_s1_reassure": (15, "Early recurrent stroke risk remains substantial after a recent carotid-territory TIA."),
        "car_s1_thrombolysis": (12, "Resolved symptoms four days earlier are not an indication for delayed intravenous thrombolysis."),
        "car_s3_delay_months": (15, "The benefit of carotid intervention is greatest when performed early after symptoms."),
        "car_s3_stop_antiplatelet": (10, "Withholding all preventive therapy leaves avoidable early stroke risk."),
        "car_s4_observe": (15, "Medical therapy alone misses indicated early revascularization in this suitable patient."),
        "car_s4_late": (15, "A six-month delay forfeits the time-dependent benefit of intervention."),
    },
    criteria=(
        "NASCET 70–99% narrowing is severe; the recent ipsilateral TIA makes the lesion symptomatic.",
        "Timing depends on neurological stability, infarct size, haemorrhage, anatomy, and procedural risk.",
    ),
    pathway=(
        "Treat a resolved focal deficit as a time-sensitive TIA rather than reassurance.",
        "Confirm ipsilateral stenosis severity and brain findings with reliable imaging.",
        "Start optimized medical prevention immediately and assess procedural suitability.",
        "Prefer early endarterectomy for suitable severe symptomatic stenosis; individualize stenting alternatives.",
    ),
    diagnosis="Recently symptomatic severe left internal carotid artery stenosis after transient ischaemic attack.",
    learning=(
        "A normal examination after a TIA does not remove early recurrent stroke risk.",
        "Laterality, NASCET severity, brain imaging, and functional status guide intervention.",
        "For suitable patients, carotid endarterectomy provides greatest benefit when performed early.",
    ),
    references=(
        _reference("ESVS 2023 Clinical Practice Guidelines on carotid and vertebral artery disease", "https://esvs.org/wp-content/uploads/2023/03/ESVS-2023-Carotid-guidelines.pdf"),
    ),
)


RAAA_CASE = _case(
    case_id="ruptured_infrarenal_aaa",
    title="Collapse with back and abdominal pain",
    category="Aortic emergencies",
    difficulty="Advanced",
    presentation=(
        "A 76-year-old man collapses with abrupt abdominal and back pain. He is pale and clammy with blood pressure 78/46 mmHg, "
        "a tender pulsatile abdominal mass, and no history of major trauma. He remains conscious but confused."
    ),
    stages=(
        _stage(
            1,
            "Initial recognition and focused assessment",
            "Haemorrhage recognition",
            "Two large-bore intravenous lines are obtained. The patient has ongoing shock but can still answer simple questions.",
            "What should happen next?",
            (
                ("raaa_s1_activate", "Activate vascular, anaesthetic, theatre/endovascular, and blood-bank pathways immediately; use balanced blood-product resuscitation and permissive hypotension while maintaining mentation."),
                ("raaa_s1_crystalloid", "Give several litres of crystalloid rapidly to normalize systolic pressure before referral."),
                ("raaa_s1_routine_ct", "Place the patient in a routine CT queue before alerting vascular services."),
                ("raaa_s1_observe", "Observe for two hours to confirm persistent hypotension."),
            ),
        ),
        _stage(
            2,
            "Severity and anatomical interpretation",
            "Imaging without delay",
            "After initial blood products the systolic pressure is 86 mmHg with preserved mentation. A CT scanner beside the emergency theatre is immediately available.",
            "Which anatomical assessment is appropriate?",
            (
                ("raaa_s2_cta", "Obtain immediate CTA only because it will not delay haemorrhage control, using it to plan endovascular versus open repair while the team mobilizes."),
                ("raaa_s2_ct_delay", "Complete a prolonged multiphase CT protocol before activating the repair team."),
                ("raaa_s2_mri", "Request MRI to avoid iodinated contrast before any intervention."),
                ("raaa_s2_elective_us", "Arrange outpatient ultrasound after blood pressure normalizes."),
            ),
        ),
        _stage(
            3,
            "Investigations and immediate management",
            "Damage-control resuscitation",
            "CTA shows an infrarenal aneurysm with retroperitoneal haemorrhage and anatomy that may permit endovascular repair. Shock persists.",
            "Which immediate-management bundle is best?",
            (
                ("raaa_s3_damage_control", "Continue rapid blood-product resuscitation, warming, calcium/coagulation monitoring, antibiotics, and immediate transfer for repair with proximal-control capability."),
                ("raaa_s3_normalize_bp", "Delay transfer until crystalloid and vasopressors normalize blood pressure."),
                ("raaa_s3_wait_coags", "Wait for every laboratory result and correction before entering theatre."),
                ("raaa_s3_ward", "Admit to a ward for serial haemoglobin measurements."),
            ),
        ),
        _stage(
            4,
            "Definitive management and escalation",
            "Emergency aneurysm repair",
            "An experienced team can perform either endovascular or open repair immediately. Anatomy, physiology, and resources are reviewed together.",
            "What is the definitive strategy?",
            (
                ("raaa_s4_repair", "Proceed immediately with endovascular repair when anatomically suitable or open repair when required; monitor for abdominal compartment syndrome and organ ischaemia."),
                ("raaa_s4_elective", "Stabilize for several days and book elective aneurysm repair."),
                ("raaa_s4_no_proximal", "Explore without planning proximal aortic control or massive-haemorrhage support."),
                ("raaa_s4_observe", "Continue observation because retroperitoneal bleeding can tamponade permanently."),
            ),
        ),
    ),
    correct=("raaa_s1_activate", "raaa_s2_cta", "raaa_s3_damage_control", "raaa_s4_repair"),
    critical=("raaa_s1_activate", "raaa_s2_cta", "raaa_s3_damage_control", "raaa_s4_repair"),
    unsafe={
        "raaa_s1_crystalloid": (12, "Aggressive crystalloid normalization can worsen bleeding, dilution, and hypothermia."),
        "raaa_s1_routine_ct": (15, "Team activation and haemorrhage control must not wait for routine imaging workflows."),
        "raaa_s2_ct_delay": (15, "Imaging is acceptable only when it does not delay repair and resuscitation."),
        "raaa_s2_mri": (15, "MRI is inappropriate in haemorrhagic shock and delays definitive control."),
        "raaa_s3_normalize_bp": (15, "Delaying repair to normalize pressure may increase haemorrhage."),
        "raaa_s3_ward": (15, "Ongoing shock with retroperitoneal bleeding requires immediate repair, not ward observation."),
        "raaa_s4_elective": (15, "A ruptured aneurysm cannot be deferred to elective repair."),
        "raaa_s4_observe": (15, "Temporary tamponade is unstable and does not replace definitive haemorrhage control."),
    },
    criteria=(
        "Shock, abdominal or back pain, and an aneurysm/retroperitoneal haemorrhage define a time-critical rupture pathway.",
        "CTA is useful in responsive patients only when it does not delay immediate repair.",
    ),
    pathway=(
        "Recognize catastrophic internal haemorrhage and activate all definitive resources at once.",
        "Use permissive hypotension and balanced blood products while preserving end-organ perfusion.",
        "Acquire rapid CTA only when it genuinely informs repair without delay.",
        "Choose immediate endovascular or open repair from anatomy, physiology, expertise, and availability.",
    ),
    diagnosis="Ruptured infrarenal abdominal aortic aneurysm with haemorrhagic shock.",
    learning=(
        "Resuscitation, imaging, and definitive-team activation must occur in parallel.",
        "Permissive hypotension avoids dislodging clot while adequate mentation and perfusion are maintained.",
        "The fastest suitable repair depends on anatomy and immediately available expertise.",
    ),
    references=(
        _reference("ESVS 2024 Clinical Practice Guidelines on abdominal aorto-iliac artery aneurysms", "https://esvs.org/wp-content/uploads/2024/02/ESVS-2024-AAA-Guidelines.pdf"),
    ),
)


POPLITEAL_CASE = _case(
    case_id="thrombosed_popliteal_aneurysm_ali",
    title="The cold leg with a popliteal mass",
    category="Arterial emergencies",
    difficulty="Advanced",
    presentation=(
        "A 66-year-old man develops eight hours of left foot pain and coldness. He previously had a right popliteal aneurysm repair. "
        "The left popliteal pulse was once described as prominent, but it is now absent."
    ),
    stages=(
        _stage(
            1,
            "Initial recognition and focused assessment",
            "Recognition and first actions",
            "The foot is cool with absent pedal signals. There is no active bleeding or contraindication to heparin.",
            "What is the best initial pathway?",
            (
                ("paa_s1_urgent", "Suspect acute thrombosis of an aneurysmal segment, give IV unfractionated heparin, and involve the vascular team urgently."),
                ("paa_s1_compress", "Apply compression over the popliteal fossa and observe."),
                ("paa_s1_outpatient", "Arrange surveillance ultrasound in three months."),
                ("paa_s1_dvt_only", "Treat empirically for venous thrombosis without arterial assessment."),
            ),
        ),
        _stage(
            2,
            "Severity and limb viability",
            "Rutherford classification",
            "There is numbness limited to the toes, no motor weakness, an absent arterial Doppler signal, and a present venous signal.",
            "How should this limb be classified?",
            (
                ("paa_s2_iia", "Marginally threatened (Rutherford IIa): salvageable with prompt treatment and no motor deficit."),
                ("paa_s2_i", "Viable, so no urgent treatment is needed."),
                ("paa_s2_iib", "Immediately threatened despite the absence of motor deficit."),
                ("paa_s2_iii", "Irreversible, requiring primary amputation."),
            ),
        ),
        _stage(
            3,
            "Investigations and immediate management",
            "Aneurysm and runoff definition",
            "The limb remains stable after heparin. Rapid CTA can define the aneurysm, distal runoff, and inflow without delaying treatment.",
            "What is the best investigation and early-treatment plan?",
            (
                ("paa_s3_runoff", "Obtain urgent anatomical/runoff imaging; consider catheter-directed thrombolysis or thrombectomy to restore runoff in this salvageable limb while planning aneurysm exclusion."),
                ("paa_s3_delay", "Wait several days on anticoagulation before defining anatomy."),
                ("paa_s3_no_runoff", "Plan aneurysm exclusion without assessing or restoring distal runoff."),
                ("paa_s3_biopsy", "Biopsy the popliteal mass before vascular imaging."),
            ),
        ),
        _stage(
            4,
            "Definitive management and escalation",
            "Aneurysm exclusion and revascularization",
            "Imaging confirms thrombosis through a popliteal aneurysm with recoverable distal targets after thrombus treatment.",
            "Which definitive plan is most appropriate?",
            (
                ("paa_s4_bypass", "Restore durable flow and exclude the aneurysm—often with bypass plus ligation/exclusion—tailored to conduit, runoff, anatomy, and expertise."),
                ("paa_s4_anticoag_only", "Discharge on anticoagulation alone despite the threatened limb and thrombosed aneurysm."),
                ("paa_s4_ligate_only", "Ligate the aneurysm without providing distal revascularization."),
                ("paa_s4_delay", "Defer repair until the limb develops motor weakness."),
            ),
        ),
    ),
    correct=("paa_s1_urgent", "paa_s2_iia", "paa_s3_runoff", "paa_s4_bypass"),
    critical=("paa_s1_urgent", "paa_s2_iia", "paa_s3_runoff", "paa_s4_bypass"),
    unsafe={
        "paa_s1_compress": (10, "Compression does not treat aneurysm thrombosis and can worsen arterial perfusion."),
        "paa_s1_outpatient": (15, "An acutely ischaemic limb requires urgent assessment, not surveillance."),
        "paa_s2_iii": (15, "Sensory loss limited to toes without paralysis is not irreversible ischaemia."),
        "paa_s3_delay": (12, "Delay risks propagation and loss of distal runoff."),
        "paa_s3_no_runoff": (12, "Durable repair depends on understanding and restoring distal runoff."),
        "paa_s4_anticoag_only": (15, "Anticoagulation alone does not correct the threatened limb or aneurysm source."),
        "paa_s4_ligate_only": (15, "Exclusion without revascularization leaves the limb underperfused."),
        "paa_s4_delay": (15, "Waiting for motor weakness allows progression to a more threatened limb."),
    },
    criteria=(
        "Rutherford IIa has sensory change limited to the toes, no motor deficit, and absent arterial with present venous Doppler signals.",
        "A thrombosed popliteal aneurysm requires assessment of thrombus burden and distal runoff.",
    ),
    pathway=(
        "Recognize an aneurysmal source of acute limb ischaemia and anticoagulate promptly.",
        "Use sensory and motor findings to classify viability.",
        "Define inflow, aneurysm anatomy, and distal runoff; restore runoff when appropriate.",
        "Exclude the aneurysm and establish durable limb perfusion.",
    ),
    diagnosis="Thrombosed left popliteal artery aneurysm causing Rutherford IIa acute limb ischaemia.",
    learning=(
        "Prior contralateral aneurysm raises suspicion for bilateral popliteal disease.",
        "Runoff restoration may be central to limb salvage before durable aneurysm repair.",
        "Definitive care must both restore flow and exclude the embolic/thrombotic aneurysm source.",
    ),
    references=(
        _reference("SVS Clinical Practice Guidelines on popliteal artery aneurysms", "https://vascular.org/news-advocacy/articles-press-releases/society-vascular-surgery-releases-clinical-practice-0"),
    ),
)


PHLEGMASIA_CASE = _case(
    case_id="iliofemoral_dvt_phlegmasia",
    title="The rapidly swollen blue leg",
    category="Venous emergencies",
    difficulty="Advanced",
    presentation=(
        "A 54-year-old woman receiving treatment for a fictional malignancy develops rapid swelling, severe pain, and blue discoloration of the entire left leg over six hours. "
        "She is tachycardic and mildly hypotensive; arterial Doppler signals are present but weak from oedema."
    ),
    stages=(
        _stage(
            1,
            "Initial recognition and focused assessment",
            "Recognition and limb threat",
            "The leg is tense and cyanotic from groin to foot. Capillary refill is delayed, and swelling is far greater than the other side.",
            "What is the safest initial response?",
            (
                ("phl_s1_urgent", "Treat as limb- and life-threatening massive venous obstruction: resuscitate, elevate, anticoagulate unless contraindicated, and obtain urgent vascular/venous intervention review."),
                ("phl_s1_diuretic", "Give a diuretic and arrange outpatient review for dependent oedema."),
                ("phl_s1_no_heparin", "Withhold anticoagulation because cyanosis proves an arterial-only process."),
                ("phl_s1_walk", "Encourage vigorous walking before imaging to mobilize the thrombus."),
            ),
        ),
        _stage(
            2,
            "Severity and anatomical interpretation",
            "Massive venous occlusion",
            "Duplex shows occlusive thrombus from the common femoral vein proximally; the iliac veins are not fully visualized. The leg remains cyanotic and painful.",
            "How should this be interpreted?",
            (
                ("phl_s2_phlegmasia", "Extensive iliofemoral obstruction with phlegmasia and threatened microcirculation; define proximal extent urgently."),
                ("phl_s2_simple_dvt", "Uncomplicated calf DVT suitable for routine outpatient care."),
                ("phl_s2_cellulitis", "Cellulitis alone; stop vascular assessment."),
                ("phl_s2_arterial_amp", "Irreversible arterial gangrene requiring immediate amputation without venous treatment."),
            ),
        ),
        _stage(
            3,
            "Investigations and immediate management",
            "Venous imaging and stabilization",
            "There is no active bleeding or recent intracranial event. Cross-sectional venous imaging can be obtained rapidly while the intervention team mobilizes.",
            "Which plan is most appropriate?",
            (
                ("phl_s3_anticoag_image", "Continue therapeutic heparin, resuscitation and elevation; use urgent CT/MR venography or venography to define iliocaval extent without delaying limb-saving treatment."),
                ("phl_s3_compression_only", "Use compression stockings alone and withhold anticoagulation."),
                ("phl_s3_wait_week", "Wait one week for swelling to settle before proximal imaging."),
                ("phl_s3_arteriogram", "Perform isolated arterial angiography and ignore the proven venous thrombosis."),
            ),
        ),
        _stage(
            4,
            "Definitive management and escalation",
            "Thrombus removal for limb threat",
            "Despite heparin the cyanosis and pain progress. Imaging confirms extensive iliocaval thrombus; bleeding risk is acceptable and an experienced team is available.",
            "What is the best escalation?",
            (
                ("phl_s4_remove", "Escalate to urgent catheter-based thrombus removal, with thrombolysis when appropriate, treat an underlying obstruction, and assess for compartment syndrome."),
                ("phl_s4_heparin_only", "Continue anticoagulation alone despite progressive threatened perfusion."),
                ("phl_s4_delay", "Delay intervention until skin necrosis is established."),
                ("phl_s4_filter_only", "Insert an inferior vena cava filter as sole treatment despite no anticoagulation contraindication."),
            ),
        ),
    ),
    correct=("phl_s1_urgent", "phl_s2_phlegmasia", "phl_s3_anticoag_image", "phl_s4_remove"),
    critical=("phl_s1_urgent", "phl_s2_phlegmasia", "phl_s4_remove"),
    unsafe={
        "phl_s1_diuretic": (15, "Diuresis and outpatient delay do not treat massive venous obstruction and threatened perfusion."),
        "phl_s1_no_heparin": (12, "Cyanosis in phlegmasia does not justify withholding indicated anticoagulation."),
        "phl_s2_arterial_amp": (15, "The presentation is potentially reversible venous outflow obstruction, not an automatic indication for amputation."),
        "phl_s3_compression_only": (15, "Compression alone is inadequate for acute limb-threatening iliofemoral thrombosis."),
        "phl_s3_wait_week": (15, "Delay risks venous gangrene and systemic deterioration."),
        "phl_s4_heparin_only": (15, "Progressive limb threat despite anticoagulation warrants urgent thrombus-removal assessment."),
        "phl_s4_delay": (15, "Waiting for necrosis abandons the opportunity for limb salvage."),
        "phl_s4_filter_only": (10, "A filter does not relieve venous obstruction and is not sole therapy when anticoagulation is feasible."),
    },
    criteria=(
        "Phlegmasia cerulea dolens combines massive proximal venous thrombosis, severe swelling, cyanosis, and threatened arterial inflow/microcirculation.",
    ),
    pathway=(
        "Recognize cyanotic massive swelling as a venous limb emergency.",
        "Begin anticoagulation and resuscitation while defining iliofemoral/iliocaval extent.",
        "Monitor perfusion and compartment pressure rather than assuming a simple calf DVT.",
        "Escalate progressive limb threat to prompt thrombus removal in an experienced centre.",
    ),
    diagnosis="Extensive iliofemoral deep-vein thrombosis with phlegmasia cerulea dolens.",
    learning=(
        "Severe venous outflow obstruction can compromise arterial inflow and threaten the limb.",
        "Therapeutic anticoagulation begins promptly unless contraindicated.",
        "Progression despite anticoagulation can justify urgent catheter-based thrombus removal after bleeding-risk assessment.",
    ),
    references=(
        _reference("ESVS 2021 Clinical Practice Guidelines on venous thrombosis", "https://www.sciencedirect.com/science/article/pii/S1078588420308686"),
    ),
)


TRAUMA_CASE = _case(
    case_id="penetrating_femoral_artery_trauma",
    title="Bleeding from a thigh wound",
    category="Vascular trauma",
    difficulty="Advanced",
    presentation=(
        "A 29-year-old adult arrives immediately after a fictional penetrating injury to the upper thigh. Bright-red pulsatile bleeding resumes when a soaked dressing is lifted. "
        "There is an expanding groin haematoma, absent pedal pulses, tachycardia, and hypotension."
    ),
    stages=(
        _stage(
            1,
            "Initial recognition and focused assessment",
            "Haemorrhage control",
            "The patient is conscious but deteriorating. The wound is below the inguinal ligament and no impaled object remains.",
            "What is the first priority?",
            (
                ("tra_s1_control", "Apply direct pressure or a correctly positioned tourniquet, activate trauma/vascular and massive-transfusion pathways, and move toward immediate operative control."),
                ("tra_s1_blind_clamp", "Probe the wound and apply blind clamps in the emergency department."),
                ("tra_s1_remove_pressure", "Repeatedly remove pressure dressings to inspect the bleeding point."),
                ("tra_s1_ct_first", "Send the unstable patient for routine CTA before haemorrhage control or team activation."),
            ),
        ),
        _stage(
            2,
            "Severity and anatomical interpretation",
            "Hard signs of vascular injury",
            "Pulsatile haemorrhage, an expanding haematoma, distal ischaemia, and shock are all present.",
            "What do these findings require?",
            (
                ("tra_s2_hard_signs", "Treat as hard signs of major arterial injury requiring immediate operative exploration without delaying for diagnostic imaging."),
                ("tra_s2_soft_signs", "Treat as soft signs only and observe with serial examinations."),
                ("tra_s2_abi", "Delay exploration until exercise ABI testing is completed."),
                ("tra_s2_discharge", "Discharge if bleeding stops under pressure."),
            ),
        ),
        _stage(
            3,
            "Investigations and immediate management",
            "Damage-control preparation",
            "The operating room is ready. The patient has received warmed blood products; broad contamination and associated venous injury remain possible.",
            "Which operative-preparation plan is best?",
            (
                ("tra_s3_prepare", "Continue damage-control resuscitation, give antibiotics and tetanus prophylaxis, prepare proximal/distal control, and consider a temporary shunt if physiology or associated injuries demand it."),
                ("tra_s3_wait_ct", "Keep pressure on the wound while waiting for a detailed CTA reconstruction."),
                ("tra_s3_no_blood", "Use crystalloid alone and defer blood products until haemoglobin returns."),
                ("tra_s3_no_venous", "Ignore possible venous and soft-tissue injuries during planning."),
            ),
        ),
        _stage(
            4,
            "Definitive management and escalation",
            "Arterial repair and limb surveillance",
            "Exploration shows a destructive common femoral arterial injury with viable distal muscle and a repairable segment. The patient responds to resuscitation.",
            "What is the preferred definitive strategy?",
            (
                ("tra_s4_repair", "Obtain proximal/distal control and restore flow with primary repair or interposition graft, address associated injuries, and monitor for compartment syndrome with fasciotomy when indicated."),
                ("tra_s4_ligate", "Ligate the common femoral artery and close without assessing limb perfusion."),
                ("tra_s4_observe", "Pack the wound and observe without definitive arterial control."),
                ("tra_s4_primary_amp", "Perform primary amputation despite viable tissue and a feasible repair."),
            ),
        ),
    ),
    correct=("tra_s1_control", "tra_s2_hard_signs", "tra_s3_prepare", "tra_s4_repair"),
    critical=("tra_s1_control", "tra_s2_hard_signs", "tra_s3_prepare", "tra_s4_repair"),
    unsafe={
        "tra_s1_blind_clamp": (15, "Blind clamping can worsen arterial, venous, and nerve injury."),
        "tra_s1_remove_pressure": (12, "Repeatedly releasing effective pressure can precipitate uncontrolled haemorrhage."),
        "tra_s1_ct_first": (15, "Hard signs with instability require haemorrhage control, not diagnostic delay."),
        "tra_s2_discharge": (15, "Temporary control does not remove the hard signs of major vascular injury."),
        "tra_s3_wait_ct": (15, "CTA must not delay exploration when hard signs and shock are present."),
        "tra_s3_no_blood": (12, "Crystalloid-only resuscitation is unsafe in major traumatic haemorrhage."),
        "tra_s4_ligate": (15, "Common femoral ligation without revascularization creates severe limb ischaemia when repair is feasible."),
        "tra_s4_observe": (15, "Packing alone does not provide definitive arterial control or restore distal perfusion."),
        "tra_s4_primary_amp": (15, "Viable tissue and a feasible repair make immediate amputation inappropriate."),
    },
    criteria=(
        "Hard signs include active/pulsatile haemorrhage, expanding haematoma, absent distal pulse/ischaemia, bruit/thrill, and shock attributable to vascular injury.",
    ),
    pathway=(
        "Control external haemorrhage immediately and resuscitate with blood products.",
        "Hard signs mandate exploration without a diagnostic-imaging delay.",
        "Plan proximal and distal control, damage-control shunting when needed, and associated-injury management.",
        "Restore arterial continuity whenever feasible and surveil the reperfused limb.",
    ),
    diagnosis="Penetrating common femoral artery injury with hard signs and haemorrhagic shock.",
    learning=(
        "Direct pressure and appropriate tourniquet use precede definitive operative control.",
        "Hard signs of extremity vascular injury bypass routine diagnostic imaging.",
        "Damage-control shunts can preserve perfusion when definitive repair must wait.",
    ),
    references=(
        _reference("ESVS 2025 Clinical Practice Guidelines on vascular trauma", "https://esvs.org/wp-content/uploads/2025/01/2025-Vascular-Trauma-Guidelines.pdf"),
    ),
)


MESENTERIC_CASE = _case(
    case_id="embolic_acute_mesenteric_ischaemia",
    title="Pain out of proportion",
    category="Visceral vascular emergencies",
    difficulty="Advanced",
    presentation=(
        "A 74-year-old woman with atrial fibrillation and no current anticoagulation develops sudden severe central abdominal pain. "
        "She is distressed, but the abdomen is initially soft with much less tenderness than the reported pain."
    ),
    stages=(
        _stage(
            1,
            "Initial recognition and focused assessment",
            "Recognition and urgent imaging",
            "She is tachycardic with mild metabolic acidosis. Lactate is only slightly raised; there is no peritonism.",
            "What is the best immediate pathway?",
            (
                ("ami_s1_suspect", "Suspect acute intestinal arterial ischaemia, resuscitate, obtain urgent CTA, involve surgery/vascular specialists, and start broad-spectrum antibiotics and heparin unless contraindicated."),
                ("ami_s1_wait_lactate", "Wait for a markedly elevated lactate before ordering vascular imaging."),
                ("ami_s1_endoscopy", "Arrange routine endoscopy as the first diagnostic test."),
                ("ami_s1_discharge", "Discharge with analgesia because the abdomen is soft."),
            ),
        ),
        _stage(
            2,
            "Severity and anatomical interpretation",
            "CTA interpretation",
            "CTA shows an abrupt superior mesenteric artery filling defect several centimetres from its origin. There is no free air or established pneumatosis; the proximal jejunum and colon enhance.",
            "How should these findings be interpreted?",
            (
                ("ami_s2_embolus", "An embolic occlusion with potentially salvageable bowel; absence of late CT signs does not permit delay."),
                ("ami_s2_chronic", "Incidental chronic disease that needs only outpatient follow-up."),
                ("ami_s2_ruled_out", "No pneumatosis rules out clinically important ischaemia."),
                ("ami_s2_venous", "The arterial filling defect proves isolated mesenteric venous thrombosis."),
            ),
        ),
        _stage(
            3,
            "Investigations and immediate management",
            "Resuscitation and bowel assessment",
            "Pain continues. The patient has no peritoneal signs and no anticoagulation contraindication. Endovascular and open expertise are both on site.",
            "Which immediate-management bundle is best?",
            (
                ("ami_s3_bundle", "Continue heparin, fluids guided by perfusion, broad-spectrum antibiotics, bowel rest, serial examination/lactate, and immediate multidisciplinary revascularization planning."),
                ("ami_s3_oral_contrast", "Delay treatment for an oral-contrast CT protocol."),
                ("ami_s3_antibiotics_only", "Use antibiotics and observation without restoring arterial flow."),
                ("ami_s3_wait_peritonitis", "Wait for peritonitis before involving a surgical team."),
            ),
        ),
        _stage(
            4,
            "Definitive management and escalation",
            "Revascularization and bowel viability",
            "The embolus is technically accessible, and the patient remains without overt peritonitis. Immediate endovascular and open rescue options are available.",
            "What is the definitive strategy?",
            (
                ("ami_s4_revascularize", "Restore mesenteric flow urgently by the fastest suitable endovascular or open approach, assess bowel viability, resect only non-viable bowel, and plan second look when uncertain."),
                ("ami_s4_observe", "Observe on anticoagulation alone because peritonitis is absent."),
                ("ami_s4_systemic_lysis", "Use routine systemic thrombolysis and avoid bowel assessment."),
                ("ami_s4_resect_all", "Resect all bowel supplied by the vessel without assessing viability or restoring flow."),
            ),
        ),
    ),
    correct=("ami_s1_suspect", "ami_s2_embolus", "ami_s3_bundle", "ami_s4_revascularize"),
    critical=("ami_s1_suspect", "ami_s2_embolus", "ami_s3_bundle", "ami_s4_revascularize"),
    unsafe={
        "ami_s1_wait_lactate": (15, "A normal or modest lactate does not exclude early intestinal ischaemia."),
        "ami_s1_discharge": (15, "Pain out of proportion with embolic risk requires emergency evaluation."),
        "ami_s2_ruled_out": (12, "Absence of pneumatosis does not exclude early reversible ischaemia."),
        "ami_s3_oral_contrast": (15, "Oral contrast can delay CTA and treatment and is not required for vascular assessment."),
        "ami_s3_wait_peritonitis": (15, "Peritonitis is a late sign of infarction; waiting loses salvage time."),
        "ami_s4_observe": (15, "Arterial occlusion with ongoing symptoms requires urgent restoration of flow."),
        "ami_s4_systemic_lysis": (12, "Routine systemic thrombolysis is not a substitute for targeted revascularization and bowel assessment."),
        "ami_s4_resect_all": (15, "Resection should conserve viable bowel and accompany restoration of perfusion when possible."),
    },
    criteria=(
        "Sudden pain out of proportion, an embolic risk source, and an SMA filling defect support acute embolic intestinal ischaemia.",
        "Peritonitis suggests bowel necrosis and mandates immediate laparotomy; its absence does not justify delay.",
    ),
    pathway=(
        "Maintain suspicion despite a soft abdomen or early lactate.",
        "Obtain CTA without oral contrast and involve revascularization and bowel-surgery expertise early.",
        "Give heparin, antibiotics, and perfusion-guided resuscitation while preparing definitive treatment.",
        "Revascularize first when feasible, assess bowel viability, and use second-look surgery when viability is uncertain.",
    ),
    diagnosis="Acute embolic superior mesenteric artery ischaemia with potentially viable bowel.",
    learning=(
        "Pain out of proportion and atrial fibrillation should trigger urgent CTA even before late laboratory abnormalities.",
        "Broad-spectrum antibiotics are started early because mucosal barrier failure occurs with ischaemia.",
        "Treatment pairs urgent revascularization with conservative bowel-viability assessment.",
    ),
    references=(
        _reference("WSES 2022 updated guidelines on acute mesenteric ischemia", "https://pmc.ncbi.nlm.nih.gov/articles/PMC9580452/"),
    ),
)


CASES: tuple[VascularCase, ...] = (
    ALI_CASE,
    CLTI_CASE,
    CAROTID_CASE,
    RAAA_CASE,
    POPLITEAL_CASE,
    PHLEGMASIA_CASE,
    TRAUMA_CASE,
    MESENTERIC_CASE,
)

CASES_BY_ID = {case.case_id: case for case in CASES}
if len(CASES_BY_ID) != len(CASES):
    raise ValueError("Case IDs must be globally unique")

CATEGORIES = tuple(sorted({case.category for case in CASES}))


def get_case(case_id: str) -> VascularCase:
    try:
        return CASES_BY_ID[case_id]
    except KeyError as exc:
        raise KeyError(f"Unknown vascular case: {case_id}") from exc


def filter_cases(category: str | None = None) -> tuple[VascularCase, ...]:
    if category is None:
        return CASES
    return tuple(case for case in CASES if case.category == category)


def select_case(
    *,
    mode: str,
    completed_case_ids: Sequence[str] = (),
    previous_case_id: str | None = None,
    category: str | None = None,
    specific_case_id: str | None = None,
    rng: random.Random | random.SystemRandom | None = None,
) -> tuple[VascularCase, set[str]]:
    """Select a case and return history normalized after an eligible-set reset."""
    history = set(completed_case_ids) & set(CASES_BY_ID)
    if mode == "Choose a specific case":
        if not specific_case_id:
            raise ValueError("A specific case ID is required")
        return get_case(specific_case_id), history

    eligible = filter_cases(category if mode == "Choose category" else None)
    if not eligible:
        raise ValueError("No cases are available for the selected category")

    eligible_ids = {case.case_id for case in eligible}
    remaining = [case for case in eligible if case.case_id not in history]
    if not remaining:
        history -= eligible_ids
        remaining = list(eligible)

    non_repeating = [case for case in remaining if case.case_id != previous_case_id]
    if non_repeating:
        remaining = non_repeating

    chooser = rng or random.SystemRandom()
    return chooser.choice(remaining), history
