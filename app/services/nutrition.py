import requests

try:
    import easyocr
except Exception:
    easyocr = None

BASE_URL = "https://world.openfoodfacts.net/api/v2/product"

reader = None


def get_ocr_reader():
    """
    Lazily initialize EasyOCR.

    This prevents the OCR model from loading when
    OCR is not required.
    """

    global reader

    if reader is None:

        if easyocr is None:
            return None

        reader = easyocr.Reader(
            ["en"],
            gpu=False
        )

    return reader


def get_product(barcode: str):
    """
    Fetch product information from OpenFoodFacts.
    """

    if not barcode:
        return None

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

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent":
                    "HealthShield-Hackathon/1.0"
            },
            timeout=10
        )

        if response.status_code != 200:
            return None

        data = response.json()

        if data.get("status") != 1:
            return None

        return data.get("product")

    except requests.RequestException:
        return None

    except Exception:
        return None


def calculate_safety_score(product, profile):

    score = 10.0
    warnings = []

    nutriments = product.get(
        "nutriments",
        {}
    ) or {}

    sugars = nutriments.get(
        "sugars_100g",
        0
    ) or 0

    salt = nutriments.get(
        "salt_100g",
        0
    ) or 0

    ingredients = (
        product.get(
            "ingredients_text",
            ""
        ) or ""
    ).lower()

    allergens = (
        product.get(
            "allergens",
            ""
        ) or ""
    ).lower()

    nova = product.get(
        "nova_group"
    )

    # Diabetes
    if profile.diabetes and sugars > 10:

        score -= 3

        warnings.append(
            "High sugar (diabetes risk)"
        )

    # Hypertension
    if profile.hypertension and salt > 1.2:

        score -= 2

        warnings.append(
            "High salt (hypertension risk)"
        )

    # Lactose
    if profile.lactose_intolerant:

        lactose_words = [
            "milk",
            "lactose",
            "whey",
            "casein"
        ]

        if any(
            word in ingredients
            for word in lactose_words
        ):

            score -= 3

            warnings.append(
                "Contains milk/lactose"
            )

    # Gluten
    if profile.gluten_allergy:

        gluten_words = [
            "gluten",
            "wheat",
            "barley",
            "rye"
        ]

        if any(
            word in ingredients
            for word in gluten_words
        ) or "gluten" in allergens:

            score -= 4

            warnings.append(
                "Contains gluten"
            )

    # Nuts
    if profile.nut_allergy:

        nut_words = [
            "nuts",
            "peanut",
            "almond",
            "cashew",
            "walnut",
            "hazelnut",
            "pistachio"
        ]

        if any(
            word in ingredients
            for word in nut_words
        ):

            score -= 5

            warnings.append(
                "Contains nuts/peanuts"
            )

    # NOVA 4
    if nova == 4:

        score -= 1.5

        warnings.append(
            "Ultra-processed food"
        )

    score = max(
        0,
        round(score, 1)
    )

    return score, warnings


def extract_text_from_image(image):
    """
    Extract text from an OpenCV image using EasyOCR.

    image can be:
        - OpenCV BGR image
        - numpy array
    """

    ocr_reader = get_ocr_reader()

    if ocr_reader is None:

        raise RuntimeError(
            "EasyOCR is not installed or "
            "could not be initialized"
        )

    results = ocr_reader.readtext(
        image
    )

    text_parts = []

    for item in results:

        if len(item) >= 2:

            detected_text = item[1]

            if detected_text:
                text_parts.append(
                    detected_text
                )

    return " ".join(text_parts)