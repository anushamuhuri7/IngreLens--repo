import os

try:
    import google.generativeai as genai
except Exception:
    genai = None


# ==================================================
# ADDITIVES
# ==================================================

ULTRA_PROCESSED_ADDITIVES = {

    "e322":
        "Soy Lecithin",

    "e330":
        "Citric Acid",

    "e621":
        "Monosodium Glutamate (MSG)",

    "e950":
        "Acesulfame K",

    "e951":
        "Aspartame",

    "e955":
        "Sucralose",

    "e211":
        "Sodium Benzoate",

    "e202":
        "Potassium Sorbate",

    "e407":
        "Carrageenan",

    "e466":
        "Carboxymethyl Cellulose",

    "e471":
        "Mono and Diglycerides"
}


# ==================================================
# ADDITIVE DETECTION
# ==================================================

def detect_additives(
    text: str
):

    if not text:

        return []


    text = text.lower()

    found = []


    for code, name in (
        ULTRA_PROCESSED_ADDITIVES.items()
    ):

        if code in text:

            found.append({

                "code":
                    code.upper(),

                "name":
                    name

            })


    return found


# ==================================================
# EXPLANATION
# ==================================================

def ai_explanation(
    score,
    warnings,
    additives
):

    message = (
        f"IngreLens Score: "
        f"{score}/10.\n"
    )


    if warnings:

        message += (
            "\nPersonalized concerns:\n"
        )


        for warning in warnings:

            message += (
                f"• {warning}\n"
            )


    if additives:

        message += (
            "\nDetected additives:\n"
        )


        for additive in additives:

            message += (
                f"• {additive['code']} "
                f"({additive['name']})\n"
            )


    if score >= 8:

        message += (
            "\nThis product appears suitable "
            "for your health profile."
        )


    elif score >= 5:

        message += (
            "\nUse this product in moderation."
        )


    else:

        message += (
            "\nThis product has multiple "
            "concerns based on your health profile."
        )


    return message


# ==================================================
# GEMINI
# ==================================================

def generate_ai_reason(
    product,
    profile,
    score,
    warnings
):

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )


    if not api_key:

        return (
            "AI explanation is unavailable "
            "because GEMINI_API_KEY is not configured."
        )


    if genai is None:

        return (
            "Google Generative AI package "
            "is not installed."
        )


    try:

        genai.configure(
            api_key=api_key
        )


        model = (
            genai.GenerativeModel(
                "gemini-2.5-flash"
            )
        )


        prompt = f"""
You are the AI assistant for IngreLens.

Product:
{product}

User health profile:
Diabetes: {profile.diabetes}
Hypertension: {profile.hypertension}
Lactose intolerance: {profile.lactose_intolerant}
Gluten allergy: {profile.gluten_allergy}
Nut allergy: {profile.nut_allergy}

IngreLens score:
{score}/10

Warnings:
{warnings}

Explain the result in simple language.

Do not diagnose medical conditions.

Focus only on the available product,
ingredient and nutritional information.
"""


        response = (
            model.generate_content(
                prompt
            )
        )


        if response and response.text:

            return response.text


        return (
            "No AI explanation was generated."
        )


    except Exception:

        return (
            "AI explanation is temporarily unavailable."
        )