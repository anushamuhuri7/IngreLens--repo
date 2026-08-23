from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

import cv2
import numpy as np
import os
import uuid


# ==================================================
# QR / BARCODE
# ==================================================

try:
    from pyzbar.pyzbar import decode
except Exception:
    decode = None


# ==================================================
# APP IMPORTS
# ==================================================

from app.dependencies import (
    get_db,
    get_current_user
)

from app import models

from app.services.ai import (
    detect_additives,
    ai_explanation
)

from app.services.nutrition import (
    get_product,
    calculate_safety_score,
    extract_text_from_image
)


# ==================================================
# ROUTER
# ==================================================

router = APIRouter(
    prefix="/food",
    tags=["Food Scanner"]
)


# ==================================================
# QR / BARCODE DETECTION
# ==================================================

def detect_food_code(frame):
    """
    Detect QR code or barcode from the uploaded image.

    Returns:
        str: Detected QR/barcode value
        None: If no code was detected
    """

    # --------------------------------------------------
    # First try OpenCV QR detector
    # --------------------------------------------------

    qr_detector = cv2.QRCodeDetector()

    qr_value, points, _ = (
        qr_detector.detectAndDecode(frame)
    )

    if qr_value:
        return qr_value


    # --------------------------------------------------
    # Then try barcode detector
    # --------------------------------------------------

    if decode is not None:

        try:

            detected = decode(frame)

            if detected:

                return detected[0].data.decode(
                    "utf-8",
                    errors="ignore"
                )

        except Exception:
            pass


    # --------------------------------------------------
    # Nothing detected
    # --------------------------------------------------

    return None


# ==================================================
# FOOD SCANNER
# ==================================================

@router.post("/scan")
async def scan_food(

    image: UploadFile = File(...),

    db: Session = Depends(get_db),

    current_user: models.User = Depends(
        get_current_user
    )

):

    # ==================================================
    # READ IMAGE
    # ==================================================

    contents = await image.read()

    if not contents:

        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty"
        )


    # ==================================================
    # CONVERT IMAGE
    # ==================================================

    np_image = np.frombuffer(
        contents,
        np.uint8
    )

    frame = cv2.imdecode(
        np_image,
        cv2.IMREAD_COLOR
    )

    if frame is None:

        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )


    # ==================================================
    # SAVE IMAGE TEMPORARILY
    # ==================================================

    upload_dir = os.path.join(
        "app",
        "uploads"
    )

    os.makedirs(
        upload_dir,
        exist_ok=True
    )

    filename = f"{uuid.uuid4()}.jpg"

    filepath = os.path.join(
        upload_dir,
        filename
    )


    with open(filepath, "wb") as f:
        f.write(contents)


    try:

        # ==================================================
        # BARCODE / QR
        # ==================================================

        barcode = detect_food_code(
            frame
        )


        # ==================================================
        # OCR FALLBACK
        # ==================================================

        if not barcode:

            text = extract_text_from_image(
                filepath
            )

            additives = detect_additives(
                text
            )

            return {

                "success": True,

                "mode": "OCR",

                "ingredients_text": text,

                "detected_additives": additives,

                "message":
                    "No barcode detected. "
                    "OCR analysis completed."

            }


        # ==================================================
        # PRODUCT LOOKUP
        # ==================================================

        product = get_product(
            barcode
        )

        if not product:

            raise HTTPException(
                status_code=404,
                detail="Product not found for this barcode"
            )


        # ==================================================
        # HEALTH PROFILE
        # ==================================================

        profile = (
            db.query(
                models.HealthProfile
            )
            .filter(
                models.HealthProfile.user_id
                == current_user.id
            )
            .first()
        )

        if not profile:

            raise HTTPException(
                status_code=404,
                detail="Health profile not found"
            )


        # ==================================================
        # SAFETY SCORE
        # ==================================================

        score, warnings = (
            calculate_safety_score(
                product,
                profile
            )
        )


        # ==================================================
        # ADDITIVES
        # ==================================================

        ingredients = product.get(
            "ingredients_text",
            ""
        )

        additives = detect_additives(
            ingredients
        )


        # ==================================================
        # AI EXPLANATION
        # ==================================================

        explanation = ai_explanation(
            score,
            warnings,
            additives
        )


        # ==================================================
        # SAVE SCAN HISTORY
        # ==================================================

        scan = models.ScanHistory(

            user_id=current_user.id,

            product_name=
                product.get("product_name"),

            safety_score=score,

            risk_message=
                ", ".join(warnings)

        )

        db.add(scan)

        db.commit()


        # ==================================================
        # RESPONSE
        # ==================================================

        return {

            "success": True,

            "mode": "BARCODE",

            "barcode": barcode,

            "product_name":
                product.get("product_name"),

            "brand":
                product.get("brands"),

            "ingredients_text":
                product.get("ingredients_text"),

            "nutrition_grade":
                product.get("nutrition_grades"),

            "nova_group":
                product.get("nova_group"),

            "safety_score":
                score,

            "warnings":
                warnings,

            "detected_additives":
                additives,

            "ai_explanation":
                explanation

        }


    except HTTPException:
        # Preserve FastAPI HTTP errors
        raise


    except Exception as e:

        # Roll back database changes if something fails
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Food scan failed: {str(e)}"
        )


    finally:

        # ==================================================
        # DELETE TEMPORARY FILE
        # ==================================================

        if os.path.exists(filepath):

            try:
                os.remove(filepath)
            except Exception:
                pass