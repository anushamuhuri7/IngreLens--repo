from io import BytesIO

import cv2
import numpy as np
import requests
from PIL import Image

from app.services.rating import split_ingredients

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024


def validate_image(contents: bytes) -> None:
    if not contents or len(contents) > MAX_IMAGE_SIZE:
        raise ValueError("Image is empty or larger than 10 MB")
    try:
        with Image.open(BytesIO(contents)) as image:
            image.verify()
    except Exception as exc:
        raise ValueError("The uploaded file is not a valid image") from exc


def detect_product_code(contents: bytes) -> str | None:
    frame = cv2.imdecode(np.frombuffer(contents, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        return None
    value, _, _ = cv2.QRCodeDetector().detectAndDecode(frame)
    if value:
        return value
    # BarcodeDetector is available in OpenCV builds that include the barcode module.
    barcode_module = getattr(cv2, "barcode", None)
    if barcode_module is None:
        return None
    try:
        decoded = barcode_module.BarcodeDetector().detectAndDecode(frame)
        if isinstance(decoded, tuple):
            for item in decoded:
                if isinstance(item, str) and item:
                    return item
                if isinstance(item, (tuple, list)):
                    return next((value for value in item if isinstance(value, str) and value), None)
    except cv2.error:
        return None
    return None


def lookup_product(code: str) -> dict | None:
    try:
        response = requests.get(
            f"https://world.openfoodfacts.org/api/v2/product/{code}",
            params={"fields": "product_name,ingredients_text"},
            headers={"User-Agent": "IngreLens/1.0 (contact: admin@example.com)"},
            timeout=8,
        )
        data = response.json()
        return data.get("product") if response.ok and data.get("status") == 1 else None
    except (requests.RequestException, ValueError):
        return None


def scan_image(contents: bytes) -> tuple[str | None, list[str]]:
    """Find a QR product code and resolve its ingredient list when possible."""
    code = detect_product_code(contents)
    product = lookup_product(code) if code else None
    if not product:
        return None, []
    return product.get("product_name"), split_ingredients(product.get("ingredients_text") or "")
