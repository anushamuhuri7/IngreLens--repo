import re
import requests
from app.services.packaging import (
    analyze_image_quality,
    detect_packaging_edges,
    calculate_packaging_risk
)

# OpenFDA drug label API
OPENFDA_URL = "https://api.fda.gov/drug/label.json"


def extract_batch_number(text: str):
    if not text:
        return None

    text = text.upper()

    patterns = [r"(?:BATCH|BATCH\s*NO|BATCH\s*NUMBER)[\s.:#-]*([A-Z0-9-]+)"]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return match.group(1)

    return None


def extract_expiry(text: str):
    """
    Extract expiry date from OCR text.

    Supports formats such as:
        EXP 08/2027
        EXP: 08-2027
        EXP 08/27
        08/2027
    """

    if not text:
        return None

    text = text.upper()

    patterns = [
        r"(?:EXP|EXPIRY|EXP\. DATE)[\s.:#-]*(\d{2}[/-]\d{2,4})",
        r"(?:EXP|EXPIRY|EXP\. DATE)[\s.:#-]*(\d{4}[/-]\d{2})",
        r"\b(\d{2}[/-]\d{4})\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return match.group(1)

    return None


def extract_medicine_name(text: str):
    """
    Extract a likely medicine name from OCR text.

    This is a simple heuristic for the MVP.
    """

    if not text:
        return None

    # Common words that are unlikely to be medicine names
    ignored_words = {
        "tablet",
        "tablets",
        "capsule",
        "capsules",
        "syrup",
        "injection",
        "medicine",
        "medicines",
        "pharmaceutical",
        "limited",
        "ltd",
        "mg",
        "ml",
        "for",
        "oral",
        "use",
        "only",
        "batch",
        "lot",
        "number",
        "expiry",
        "exp",
        "date"
    }

    words = text.split()

    for word in words:

        # Remove OCR punctuation
        cleaned = re.sub(r"[^A-Za-z0-9-]", "", word)

        if not cleaned:
            continue

        if cleaned.lower() in ignored_words:
            continue

        # Ignore very short words
        if len(cleaned) < 4:
            continue

        # Ignore words containing only numbers
        if cleaned.isdigit():
            continue

        return cleaned

    return None


def verify_medicine(name: str):

    if not name:
        return None

    try:
        response = requests.get(
            OPENFDA_URL,
            params={
                "search": f'openfda.brand_name:"{name}"',
                "limit": 1
            },
            timeout=10
        )

        if response.status_code != 200:
            return None

        data = response.json()

        results = data.get("results")

        if not results:
            return None

        return results[0]

    except (requests.RequestException, ValueError):
        return None


def calculate_counterfeit_score(
    qr_found: bool,
    batch_found: bool,
    expiry_found: bool,
    verified: bool
):
    """
    Calculate counterfeit risk.

    Higher score = higher counterfeit risk.
    """

    risk = 0
    reasons = []

    # QR/Barcode verification
    if not qr_found:
        risk += 40
        reasons.append("No QR code or barcode detected")

    # Batch number
    if not batch_found:
        risk += 25
        reasons.append("Batch number not detected")

    # Expiry date
    if not expiry_found:
        risk += 15
        reasons.append("Expiry date not detected")

    # Medicine database verification
    if not verified:
        risk += 20
        reasons.append("Medicine could not be verified")

    # Never allow score above 100
    risk = min(risk, 100)

    # Confidence is inverse of risk
    confidence = 100 - risk

    return risk, confidence, reasons