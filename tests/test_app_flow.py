from streamlit.testing.v1 import AppTest


def _button(app, label):
    return next(item for item in app.button if item.label == label)


def _widget(items, label):
    return next(item for item in items if item.label == label)


def test_complete_expert_flow_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = AppTest.from_file("app.py").run(timeout=20)

    _button(app, "Start simulation").click().run(timeout=20)
    _widget(app.radio, "Most likely clinical syndrome").set_value("Acute lower-limb ischaemia")
    _widget(app.multiselect, "Select the immediate priorities").set_value([
        "Urgently activate the vascular team",
        "Start intravenous unfractionated heparin unless contraindicated",
        "Provide analgesia and establish intravenous access",
        "Keep the patient fasting and obtain urgent baseline blood tests/crossmatch",
    ])
    _button(app, "Lock answer and reveal examination").click().run(timeout=20)

    _widget(app.radio, "Rutherford acute limb ischaemia category").set_value(
        "Rutherford IIb — immediately threatened"
    )
    _widget(app.multiselect, "Which findings determine urgency?").set_value([
        "Sensory loss extending beyond the toes",
        "Mild motor weakness",
        "Absent distal arterial Doppler signal with preserved venous signal",
    ])
    _button(app, "Lock answer and plan investigations").click().run(timeout=20)

    _widget(app.radio, "Best next investigation strategy").set_value(
        "Immediate anatomical imaging only if it does not delay urgent revascularization"
    )
    _widget(
        app.multiselect,
        "Select useful parallel investigations that should not delay reperfusion",
    ).set_value([
        "Bedside continuous-wave Doppler assessment",
        "Full blood count, coagulation profile, electrolytes, creatinine and creatine kinase",
        "ECG and later embolic-source evaluation",
        "Group and crossmatch blood",
    ])
    _button(app, "Lock answer and choose management").click().run(timeout=20)

    _widget(app.radio, "Required treatment urgency").set_value("Immediate/urgent revascularization")
    _widget(app.multiselect, "Select reasonable components of the management plan").set_value([
        "Urgent surgical embolectomy/thrombectomy when anatomy and expertise favour it",
        "Urgent endovascular or hybrid thrombus-removal strategy when appropriate and immediately available",
        "Treat any underlying arterial lesion identified after thrombus removal",
        "Monitor for reperfusion injury and compartment syndrome; consider fasciotomy when indicated",
        "Investigate the embolic source and plan long-term stroke/systemic embolism prevention",
    ])
    _button(app, "Submit case for scoring").click().run(timeout=20)

    assert not app.exception
    assert [(metric.label, metric.value) for metric in app.metric] == [
        ("Total score", "100/100"),
        ("Performance band", "Excellent"),
        ("Critical omissions", "0"),
    ]
    assert any(button.label == "Download performance report (JSON)" for button in app.download_button)
