import re
from typing import List, Dict, Tuple
from app.models import UserProfile, IngredientAnalysis

INGREDIENT_DATABASE: Dict[str, Dict] = {
    "paraben": {
        "risk_level": "Hazardous", "hazard_score": 8, "category": "Preservative",
        "description": "Endocrine disruptor linked to hormone imbalances and skin sensitivity.",
        "side_effects": ["Hormone disruption", "Contact dermatitis"],
        "comedogenic": 0, "pregnancy_safe": False
    },
    "methylparaben": {
        "risk_level": "Hazardous", "hazard_score": 7, "category": "Preservative",
        "description": "Synthetic paraben preservative that may cause contact allergies.",
        "side_effects": ["Allergic reaction", "UV skin sensitivity"],
        "comedogenic": 0, "pregnancy_safe": False
    },
    "sodium lauryl sulfate": {
        "risk_level": "Caution", "hazard_score": 5, "category": "Surfactant",
        "description": "Harsh foaming agent that can strip natural skin barrier lipids.",
        "side_effects": ["Skin irritation", "Eye irritation"],
        "comedogenic": 2, "pregnancy_safe": True
    },
    "sls": {
        "risk_level": "Caution", "hazard_score": 5, "category": "Surfactant",
        "description": "Sodium Lauryl Sulfate abbreviation. Known skin irritant.",
        "side_effects": ["Skin irritation"],
        "comedogenic": 2, "pregnancy_safe": True
    },
    "fragrance": {
        "risk_level": "Caution", "hazard_score": 6, "category": "Fragrance",
        "description": "Catch-all term that may conceal unlisted synthetic sensitizers.",
        "side_effects": ["Contact allergy", "Respiratory irritation"],
        "comedogenic": 0, "pregnancy_safe": False
    },
    "parfum": {
        "risk_level": "Caution", "hazard_score": 6, "category": "Fragrance",
        "description": "Synthetic fragrance mixture.",
        "side_effects": ["Allergies", "Eczema flareups"],
        "comedogenic": 0, "pregnancy_safe": False
    },
    "aspartame": {
        "risk_level": "Caution", "hazard_score": 6, "category": "Sweetener",
        "description": "Synthetic sweetener (E951). Unsafe for individuals with PKU.",
        "side_effects": ["Headaches", "Digestive distress"],
        "comedogenic": 0, "pregnancy_safe": True
    },
    "high fructose corn syrup": {
        "risk_level": "Hazardous", "hazard_score": 7, "category": "Sweetener",
        "description": "Processed sweetener linked to metabolic stress and insulin spikes.",
        "side_effects": ["Insulin spikes", "Metabolic strain"],
        "comedogenic": 0, "pregnancy_safe": True
    },
    "niacinamide": {
        "risk_level": "Safe", "hazard_score": 1, "category": "Active / Vitamin B3",
        "description": "Strengthens skin barrier, regulates oil, and fades hyperpigmentation.",
        "side_effects": [],
        "comedogenic": 0, "pregnancy_safe": True
    },
    "glycerin": {
        "risk_level": "Safe", "hazard_score": 1, "category": "Humectant",
        "description": "Natural hydrating agent that retains moisture.",
        "side_effects": [],
        "comedogenic": 0, "pregnancy_safe": True
    },
    "tocopherol": {
        "risk_level": "Safe", "hazard_score": 1, "category": "Vitamin E / Antioxidant",
        "description": "Potent antioxidant shielding formulation from oxidation.",
        "side_effects": [],
        "comedogenic": 2, "pregnancy_safe": True
    },
    "salicylic acid": {
        "risk_level": "Caution", "hazard_score": 4, "category": "BHA Exfoliant",
        "description": "Oil-soluble beta hydroxy acid. Limit usage during pregnancy.",
        "side_effects": ["Dryness", "Peeling"],
        "comedogenic": 0, "pregnancy_safe": False
    }
}

def clean_and_tokenize(raw_text: str) -> List[str]:
    text = re.sub(r"(?i)ingredients\s*[:\-]\s*", "", raw_text)
    text = re.sub(r"[\n\r\t]+", " ", text)
    tokens = re.split(r"[,;•|/·\*\n]", text)
    return [t.strip(" .()[]{}:").strip() for t in tokens if len(t.strip()) > 1 and not t.strip().isdigit()]

def evaluate_ingredients(raw_text: str, profile: UserProfile) -> Tuple[List[IngredientAnalysis], float, str]:
    items = clean_and_tokenize(raw_text)
    analyzed_list: List[IngredientAnalysis] = []
    total_penalty = 0.0

    user_allergens_lower = [a.strip().lower() for a in profile.allergies if a.strip()]

    for item in items:
        item_lower = item.lower()
        matched = None

        for db_key, db_val in INGREDIENT_DATABASE.items():
            if db_key in item_lower or item_lower in db_key:
                matched = db_val
                break

        allergens_hit = [a for a in user_allergens_lower if a in item_lower]

        if matched:
            risk = matched["risk_level"]
            score = matched["hazard_score"]
            cat = matched["category"]
            desc = matched["description"]
            effects = list(matched.get("side_effects", []))
            comedo = matched.get("comedogenic", 0)

            if profile.is_pregnant and not matched.get("pregnancy_safe", True):
                risk = "Hazardous"
                score = max(score, 8)
                effects.append("Not recommended during pregnancy")
        else:
            is_paraben = "paraben" in item_lower
            is_sulfate = "sulfate" in item_lower or "sulphate" in item_lower

            if is_paraben:
                risk, score, cat = "Hazardous", 8, "Preservative"
                desc = "Suspected endocrine disrupting compound."
                effects = ["Hormonal disruption", "Contact allergy"]
                comedo = 0
            elif is_sulfate:
                risk, score, cat = "Caution", 5, "Surfactant"
                desc = "Strong cleansing agent that may irritate barrier."
                effects = ["Skin barrier irritation"]
                comedo = 1
            else:
                risk, score, cat = "Safe", 1, "General Ingredient"
                desc = "Standard cosmetic/food grade ingredient."
                effects = []
                comedo = 0

        if allergens_hit:
            risk = "Hazardous"
            score = 10
            effects.insert(0, f"MATCHES ALLERGEN: {', '.join(allergens_hit).upper()}")

        # Penalty scaled for a 0-10 system
        if score >= 7:
            total_penalty += 2.0
        elif score >= 4:
            total_penalty += 0.8
        else:
            total_penalty += 0.1

        analyzed_list.append(
            IngredientAnalysis(
                name=item.title(),
                risk_level=risk,
                hazard_score=score,
                category=cat,
                description=desc,
                allergens_matched=allergens_hit,
                side_effects=effects,
                comedogenic_rating=comedo
            )
        )

    # Calculate overall score on a 0.0 - 10.0 scale
    base_safety = round(max(0.0, min(10.0, 10.0 - total_penalty)), 1)

    if any(a.risk_level == "Hazardous" for a in analyzed_list):
        base_safety = min(base_safety, 5.5)

    if base_safety >= 8.0:
        verdict = "Safe"
    elif base_safety >= 5.0:
        verdict = "Moderate Risk"
    else:
        verdict = "Avoid"

    return analyzed_list, base_safety, verdict