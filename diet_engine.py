import re

BASE_DIETS = {
    "diabetes": {
        "breakfast": ["Oats porridge with cinnamon", "Boiled eggs or paneer bhurji", "Unsweetened soy/almond milk"],
        "lunch": ["Mixed veggie salad + chickpeas", "1-2 multigrain rotis + dal", "Unsweetened curd"],
        "snacks": ["Almonds/walnuts", "Sprouts chaat"],
        "dinner": ["Grilled paneer/tofu", "Stir-fry veggies", "Quinoa/low GI millet"],
        "avoid": ["Sugar, sweets, white bread, cola/soda"]
    },
    "hypertension": {
        "breakfast": ["Fruit bowl + oats", "Low-fat curd"],
        "lunch": ["Brown rice + dal + salad", "Leafy greens"],
        "snacks": ["Roasted chana", "Coconut water"],
        "dinner": ["Grilled fish/tofu", "Steamed vegetables"],
        "avoid": ["Excess salt, pickles, processed foods"]
    },
    "anemia": {
        "breakfast": ["Ragi dosa + chutney", "Spinach omelette / paneer"],
        "lunch": ["Spinach dal + roti", "Beetroot salad + citrus fruit"],
        "snacks": ["Dates + nuts", "Roasted sesame/peanuts"],
        "dinner": ["Rajma/chole + rice", "Leafy greens sabzi"],
        "avoid": ["Tea/coffee with meals (reduces iron absorption)"]
    },
    "thyroid": {
        "breakfast": ["Eggs/paneer", "Oats + flax/chia"],
        "lunch": ["Fish/chicken/tofu", "Veggies + quinoa"],
        "snacks": ["Greek yogurt/curd", "Fruit (avoid excess raw crucifers)"],
        "dinner": ["Dal + roti", "Sauteed greens"],
        "avoid": ["Excess soy (if hypothyroid), excess raw crucifers"]
    },
    "cholesterol": {
        "breakfast": ["Oats + nuts + seeds", "Green tea"],
        "lunch": ["Grilled fish/tofu", "Leafy salads + olive oil"],
        "snacks": ["Apple/pear", "Roasted chana"],
        "dinner": ["Dal + 1 roti", "Steamed/roasted veggies"],
        "avoid": ["Fried foods, trans fats, excess red meat"]
    },
    "normal": {
        "breakfast": ["Idli/Dosa with chutney", "Oats with fruits", "Boiled eggs or sprouts"],
        "lunch": ["2 rotis + dal + sabzi", "Brown rice + curd + veggies"],
        "snacks": ["Fruits (apple, papaya, orange)", "Handful of nuts"],
        "dinner": ["Vegetable soup + chapati", "Grilled paneer/fish + salad"],
        "avoid": ["Junk food, deep fried items, excessive sugar"]
    },
}

def _find_float(pattern: str, text: str):
    m = re.search(pattern, text, flags=re.I)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None

def _bp_values(text: str):
    m = re.search(r'(?:bp[:\s]*)?(\d{2,3})\s*/\s*(\d{2,3})', text, flags=re.I)
    if m:
        try:
            return float(m.group(1)), float(m.group(2))
        except Exception:
            return None, None
    return None, None

def infer_condition_from_text(text: str) -> str:
    t = text.lower()

    # Diabetes thresholds
    hba1c = _find_float(r'hba1c\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)', t)
    fpg = _find_float(r'(?:fasting\s+(?:plasma\s+)?)?glucose\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*mg/?dl', t)
    rpg = _find_float(r'(?:random\s+glucose|ppg|postprandial)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*mg/?dl', t)
    if (hba1c is not None and hba1c >= 6.5) or (fpg is not None and fpg >= 126) or (rpg is not None and rpg >= 200):
        return "diabetes"

    # Hypertension
    sbp, dbp = _bp_values(t)
    if (sbp and sbp >= 140) or (dbp and dbp >= 90):
        return "hypertension"

    # Anemia
    hb = _find_float(r'(?:hemoglobin|haemoglobin|hb)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*g/?dl', t)
    if hb is not None and hb < 12.5:
        return "anemia"

    # Thyroid
    tsh = _find_float(r'tsh\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)', t)
    if tsh is not None and (tsh > 4.5 or tsh < 0.4):
        return "thyroid"

    # Cholesterol
    total_chol = _find_float(r'(?:total\s+cholesterol|cholesterol\s*total)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)', t)
    ldl = _find_float(r'ldl\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)', t)
    tg = _find_float(r'(?:triglycerides|tg)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)', t)
    if (total_chol and total_chol >= 240) or (ldl and ldl >= 160) or (tg and tg >= 200):
        return "cholesterol"

    return "normal"

def diet_for_condition(condition: str, sample_type: str = None, pref: str = None) -> dict:
    plan = dict(BASE_DIETS.get(condition, BASE_DIETS["normal"]))
    if sample_type:
        st = sample_type.lower()
        plan.setdefault("tips", [])
        if "blood" in st:  plan["tips"].append("Hydrate well and include vitamin C-rich foods.")
        if "saliva" in st: plan["tips"].append("Avoid sugary snacks; rinse mouth after meals.")
        if "hair" in st:   plan["tips"].append("Add biotin sources: eggs, nuts, legumes.")
    if pref == "vegetarian":
        for k in ("breakfast","lunch","dinner"):
            plan[k] = [i.replace("fish", "tofu/paneer").replace("chicken", "paneer") for i in plan[k]]
    return plan
