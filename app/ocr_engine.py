"""Server-side OCR helper.

Uses Tesseract with a small preprocessing pipeline tuned for typical
food/medicine labels: greyscale → autocontrast → optional upscaling for
small images → mild sharpening. Falls back to an empty string when the
binary is missing so the scan endpoint can still respond.
"""
from __future__ import annotations

import io
import re

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract


def preprocess_image(image_bytes: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(image_bytes))
    # Correct EXIF-rotated phone photos
    image = ImageOps.exif_transpose(image)
    image = image.convert("L")

    # Upscale small photos so 8-10px labels become readable
    max_side = max(image.size)
    if max_side < 1200:
        scale = 1600 / max_side
        image = image.resize((int(image.size[0] * scale), int(image.size[1] * scale)), Image.LANCZOS)

    image = ImageOps.autocontrast(image, cutoff=2)
    image = ImageEnhance.Contrast(image).enhance(1.35)
    image = image.filter(ImageFilter.SHARPEN)
    return image


def _clean(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from a label image. Returns "" on any failure."""
    try:
        processed = preprocess_image(image_bytes)
    except Exception:
        return ""

    # Try two page-segmentation modes and keep whichever gives more content.
    best = ""
    for psm in (6, 4):  # 6=uniform block of text, 4=single column of text
        try:
            text = pytesseract.image_to_string(processed, config=f"--oem 3 --psm {psm}")
        except Exception:
            text = ""
        if len(text) > len(best):
            best = text
    return _clean(best)
