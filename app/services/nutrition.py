import requests
try:
    import easyocr
except Exception:
    easyocr = None

import cv2

BASE_URL = "https://world.openfoodfacts.net/api/v2/product"
reader = None

def get_ocr_reader():
    global reader
    if reader is None and easyocr is not None:
        reader = easyocr.Reader(["en"], gpu=False)
    return reader

def get_product(barcode: str):

    fields = ",".join([
        "product_name",
        "brands",
        "ingredients_text",
        "allergens",
        "additives_tags",
        "nova_group",
        "nutriments",
        "nutrition_grades",
        "image_url"
    ])

    url = f"{BASE_URL}/{barcode}?fields={fields}"

    response = requests.get(
        url,
        headers={
            "User-Agent": "HealthShield-Hackathon/1.0"
        },
        timeout=10
    )

    if response.status_code != 200:
        return None

    data = response.json()

    if data.get("status") != 1:
        return None

    return data["product"]
def calculate_safety_score(product, profile):

    score = 10.0
    warnings = []

    nutriments = product.get("nutriments", {})
    sugars = nutriments.get("sugars_100g", 0)
    salt = nutriments.get("salt_100g", 0)

    ingredients = (
        product.get("ingredients_text", "") or ""
    ).lower()

    allergens = (
        product.get("allergens", "") or ""
    ).lower()

    nova = product.get("nova_group")

    if profile.diabetes and sugars > 10:
        score -= 3
        warnings.append("High sugar (diabetes risk)")

    if profile.hypertension and salt > 1.2:
        score -= 2
        warnings.append("High salt (hypertension risk)")

    if profile.lactose_intolerant and "milk" in ingredients:
        score -= 3
        warnings.append("Contains milk")

    if profile.gluten_allergy and "gluten" in allergens:
        score -= 4
        warnings.append("Contains gluten")

    if profile.nut_allergy and (
        "nuts" in allergens or "peanut" in allergens
    ):
        score -= 5
        warnings.append("Contains nuts")

    if nova == 4:
        score -= 1.5
        warnings.append("Ultra-processed food")

    score = max(0, round(score, 1))

    return score, warnings
def extract_text_from_image(image_path):
    results = reader.readtext(image_path)

    text = " ".join([item[1] for item in results])

    return text