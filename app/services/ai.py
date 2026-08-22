import re
import google.generativeai as genai
import os

ULTRA_PROCESSED_ADDITIVES = {
    "e322": "Soy Lecithin",
    "e330": "Citric Acid",
    "e621": "Monosodium Glutamate (MSG)",
    "e950": "Acesulfame K",
    "e951": "Aspartame",
    "e955": "Sucralose",
    "e211": "Sodium Benzoate",
    "e202": "Potassium Sorbate",
    "e407": "Carrageenan",
    "e466": "Carboxymethyl Cellulose",
    "e471": "Mono and Diglycerides"
}
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")



def detect_additives(text: str):
    text = text.lower()

    found = []

    for code, name in ULTRA_PROCESSED_ADDITIVES.items():
        if code in text:
            found.append({
                "code": code.upper(),
                "name": name
            })

    return found


def ai_explanation(score, warnings, additives):
    message = f"HealthShield Score: {score}/10.\n"

    if warnings:
        message += "\nPersonalized concerns:\n"
        for warning in warnings:
            message += f"• {warning}\n"

    if additives:
        message += "\nUltra-processed additives detected:\n"
        for additive in additives:
            message += f"• {additive['code']} ({additive['name']})\n"

    if score >= 8:
        message += "\nThis product appears suitable for your health profile."
    elif score >= 5:
        message += "\nUse this product in moderation."
    else:
        message += "\nThis product poses multiple concerns based on your health profile."

    return message
def generate_ai_reason(product, profile, score, warnings):

    prompt = f"""
    Product:
    {product}

    User profile:
    Diabetes: {profile.diabetes}
    Hypertension: {profile.hypertension}
    Lactose: {profile.lactose_intolerant}
    Gluten: {profile.gluten_allergy}
    Nut allergy: {profile.nut_allergy}

    Score: {score}/10

    Warnings:
    {warnings}

    Explain this in simple language.
    """

    response = model.generate_content(prompt)

    return response.text