import re

DISCLAIMER = (
    "I'm a safety-focused health assistant and not a doctor. "
    "I don't provide diagnoses. If you have severe or persistent symptoms, seek medical care."
)

RED_FLAGS = [
    ("chest pain", "New or severe chest pain can be an emergency—seek urgent care."),
    ("shortness of breath", "Sudden/worsening shortness of breath can be an emergency."),
    ("loss of consciousness", "Fainting or unresponsiveness requires urgent evaluation."),
    ("confusion", "New confusion can be serious—seek urgent care."),
    ("severe headache", "Worst-ever headache or with neck stiffness—rule out emergency."),
    ("blood in stool", "Rectal bleeding or black stools need prompt medical attention."),
    ("coughing blood", "Coughing up blood is an emergency."),
    ("vomiting blood", "Vomiting blood requires urgent evaluation."),
    ("seizure", "Seizures require prompt medical care."),
    ("suicidal", "If you're thinking about harming yourself, seek immediate help or call a helpline."),
]

CANCER_AWARE = [
    ("unexplained weight loss", "Unintentional weight loss over weeks-months warrants evaluation."),
    ("lump", "New or growing lumps should be examined by a clinician."),
    ("night sweats", "Frequent drenching night sweats need medical review."),
    ("blood in urine", "Blood in urine (red/cola-colored) needs prompt testing."),
    ("persistent cough", "Cough >3 weeks warrants a checkup, esp. with smoking history."),
    ("change in bowel", "Ongoing bowel habit change (>3 weeks) should be assessed."),
]

SKIN_AWARE = [
    ("changing mole", "Use ABCDE: Asymmetry, Border irregular, Color varied, Diameter >6mm, Evolving. See a dermatologist."),
    ("new mole", "New skin spots that grow or bleed should be checked."),
    ("bleeding mole", "Bleeding or non-healing lesions need examination."),
    ("dark streak nail", "A new dark streak under a nail should be assessed."),
    ("non-healing sore", "Sores that don't heal in weeks need a check."),
]

def _contains(term, text):
    return term in text

def _extract_duration(text):
    m = re.search(r'(\d+)\s*(day|days|week|weeks|month|months)', text)
    if not m: return None
    qty = int(m.group(1)); unit = m.group(2)
    if "day" in unit: return qty
    if "week" in unit: return qty*7
    if "month" in unit: return qty*30
    return None

def triage_reply(user_text: str) -> str:
    t = user_text.lower()
    out = [DISCLAIMER]

    triggered = [f"• {msg}" for key,msg in RED_FLAGS if _contains(key,t)]
    if triggered:
        out.append("⚠️ Urgent symptoms noted:")
        out.extend(triggered)
        out.append("Please seek emergency/urgent care now.")
        return "\n".join(out)

    aware = [f"• {msg}" for key,msg in CANCER_AWARE if _contains(key,t)]
    skin  = [f"• {msg}" for key,msg in SKIN_AWARE if _contains(key,t)]

    dur_days = _extract_duration(t)
    if dur_days and dur_days >= 21:
        out.append("⏱️ Persistent symptoms ≥3 weeks—book a clinician visit.")

    if aware:
        out.append("🧭 Checks to consider (non-diagnostic):")
        out.extend(aware)
    if skin:
        out.append("🩺 Skin health tips:")
        out.extend(skin)

    out.append(
        "Next steps:\n"
        "• Track symptoms (onset, duration, triggers; photos for skin).\n"
        "• Consider a basic checkup: CBC, fasting glucose, lipid panel, thyroid profile as relevant.\n"
        "• If symptoms worsen or new red flags appear, seek urgent care."
    )
    return "\n".join(out)
