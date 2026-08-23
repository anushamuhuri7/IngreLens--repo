from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.ai import detect_additives, ai_explanation
import cv2
import numpy as np
try:
    from pyzbar.pyzbar import decode
except Exception:
    decode = None

import os
import uuid

from app.dependencies import get_db, get_current_user
from app import models
from app.services.nutrition import (
    get_product,
    calculate_safety_score,
    extract_text_from_image
)

router = APIRouter(
    prefix="/food",
    tags=["Food Scanner"]
)


@router.post("/scan")
async def scan_food(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Read uploaded image
    contents = await image.read()

    np_image = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

    # Save image temporarily for OCR
    filename = f"{uuid.uuid4()}.jpg"
    filepath = os.path.join("app", "uploads", filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    try:
        # Detect barcode
        decoded = decode(frame)

        # ---------- OCR FALLBACK ----------
        if not decoded:
            text = extract_text_from_image(filepath)
            additives = detect_additives(text)

            return {
                "mode": "OCR",
                "ingredients_text": text,
                "detected_additives": additives,
                "message": "No barcode detected. OCR analysis completed."
            }

        # Barcode found
        barcode = decoded[0].data.decode("utf-8")

        # Fetch product details
        product = get_product(barcode)

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        # Get user's health profile
        profile = db.query(models.HealthProfile).filter(
            models.HealthProfile.user_id == current_user.id
        ).first()

        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Health profile not found"
            )

        # Calculate personalized score
        score, warnings = calculate_safety_score(product, profile)

        # Detect additives
        ingredients = product.get("ingredients_text", "")
        additives = detect_additives(ingredients)

        # Generate AI explanation
        explanation = ai_explanation(score, warnings, additives)

        # Save scan history
        scan = models.ScanHistory(
            user_id=current_user.id,
            product_name=product.get("product_name"),
            safety_score=score,
            risk_message=", ".join(warnings)
        )

        db.add(scan)
        db.commit()

        # Return response
        return {
            "mode": "Barcode",
            "barcode": barcode,
            "product_name": product.get("product_name"),
            "brand": product.get("brands"),
            "nutrition_grade": product.get("nutrition_grades"),
            "nova_group": product.get("nova_group"),
            "safety_score": score,
            "warnings": warnings,
            "detected_additives": additives,
            "ai_explanation": explanation
        }

    finally:
        # Delete temporary uploaded image
        if os.path.exists(filepath):
            os.remove(filepath)