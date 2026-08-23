from app.models import HealthProfile

RISK_GROUPS = {
    "lactose_intolerant": (["milk", "lactose", "whey", "casein", "butter", "cream", "cheese"], 50, "Contains milk or lactose"),
    "gluten_allergy": (["gluten", "wheat", "barley", "rye", "malt"], 50, "Contains gluten"),
    "nut_allergy": (["peanut", "almond", "cashew", "walnut", "hazelnut", "pistachio", "nuts"], 50, "Contains nuts"),
}
DIABETES_TERMS = ["sugar", "glucose", "syrup", "dextrose", "fructose", "honey"]
HYPERTENSION_TERMS = ["salt", "sodium", "monosodium glutamate", "msg"]


def split_ingredients(value: str) -> list[str]:
    return [item.strip().lower() for item in value.replace(";", ",").split(",") if item.strip()]


def compute_rating(ingredients: list[str], profile: HealthProfile | None) -> tuple[float, list[str]]:
    score = 100
    warnings: list[str] = []
    text = " ".join(ingredients).lower()
    if profile:
        for attribute, (terms, penalty, message) in RISK_GROUPS.items():
            if getattr(profile, attribute) and any(term in text for term in terms):
                score -= penalty
                warnings.append(message)
        if profile.diabetes and any(term in text for term in DIABETES_TERMS):
            score -= 20
            warnings.append("Contains added sugar, which may raise blood glucose")
        if profile.hypertension and any(term in text for term in HYPERTENSION_TERMS):
            score -= 20
            warnings.append("Contains salt or sodium, which may affect blood pressure")
    if not warnings:
        warnings.append("No profile-specific risks detected from the available ingredients")
    return float(max(0, score)), warnings
