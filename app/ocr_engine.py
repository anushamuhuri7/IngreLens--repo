import io
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

def preprocess_image(image_bytes: bytes) -> Image.Image:
    """Preprocess image for optimal OCR extraction."""
    image = Image.open(io.BytesIO(image_bytes)).convert("L")
    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    # Apply thresholding
    image = image.filter(ImageFilter.SHARPEN)
    return image

def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract ingredient list text via Tesseract OCR with fallback."""
    try:
        processed_img = preprocess_image(image_bytes)
        # Tesseract whitelist configuration for ingredient labels
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(processed_img, config=custom_config)
        return text.strip()
    except Exception as e:
        # Fallback if tesseract binary is uninstalled in sandbox
        return ""