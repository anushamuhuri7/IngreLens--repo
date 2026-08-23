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
import uuid
import os

# --------------------------------------------------
# EasyOCR
# --------------------------------------------------

try:
    import easyocr
except Exception:
    easyocr = None


# --------------------------------------------------
# QR / Barcode
# --------------------------------------------------

try:
    from pyzbar.pyzbar import decode
except Exception:
    decode = None


# --------------------------------------------------
# App imports
# --------------------------------------------------

from app.dependencies import (
    get_db,
    get_current_user
)

from app import models

from app.services.medicine import (
    extract_batch_number,
    extract_expiry,
    extract_medicine_name,
    verify_medicine,
    calculate_counterfeit_score
)

from app.services.packaging import (
    analyze_image_quality,
    detect_packaging_edges,
    calculate_packaging_risk
)


# --------------------------------------------------
# Router
# --------------------------------------------------

router = APIRouter(
    prefix="/medicine",
    tags=["Medicine Scanner"]
)


# ==================================================
# OCR
# ==================================================

reader = None


def get_ocr_reader():
    """
    Create and return the EasyOCR reader.

    The reader is initialized only once because
    loading EasyOCR is expensive.
    """

    global reader

    if reader is None:

        if easyocr is None:
            raise HTTPException(
                status_code=500,
                detail="EasyOCR is not installed."
            )

        reader = easyocr.Reader(
            ["en"],
            gpu=False
        )

    return reader


# ==================================================
# QR / BARCODE DETECTION
# ==================================================

def detect_codes(frame):
    """
    Detect QR code or barcode from an OpenCV image.

    Returns:
        (True, value, "QR")
        (True, value, "BARCODE")
        (False, None, None)
    """

    # --------------------------------------------------
    # QR Code
    # --------------------------------------------------

    qr_detector = cv2.QRCodeDetector()

    qr_value, points, _ = qr_detector.detectAndDecode(
        frame
    )

    if qr_value:
        return True, qr_value, "QR"


    # --------------------------------------------------
    # Barcode using pyzbar
    # --------------------------------------------------

    if decode is not None:

        try:

            detected = decode(frame)

            if detected:

                value = detected[0].data.decode(
                    "utf-8",
                    errors="ignore"
                )

                return True, value, "BARCODE"

        except Exception:
            pass


    # --------------------------------------------------
    # Nothing found
    # --------------------------------------------------

    return False, None, None


# ==================================================
# MEDICINE SCAN
# ==================================================

@router.post("/scan")
async def scan_medicine(

    image: UploadFile = File(...),

    db: Session = Depends(get_db),

    current_user: models.User = Depends(
        get_current_user
    )
):

    # --------------------------------------------------
    # Read uploaded image
    # --------------------------------------------------

    contents = await image.read()

    if not contents:

        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty"
        )


    # ==================================================
    # Convert image to OpenCV format
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
    # Create temporary file
    # ==================================================

    filename = f"{uuid.uuid4()}.jpg"

    upload_dir = os.path.join(
        "app",
        "uploads"
    )

    os.makedirs(
        upload_dir,
        exist_ok=True
    )

    filepath = os.path.join(
        upload_dir,
        filename
    )


    with open(filepath, "wb") as f:
        f.write(contents)


    try:

        # ==================================================
        # QR / BARCODE
        # ==================================================

        code_found, code_value, code_type = detect_codes(
            frame
        )


        # ==================================================
        # OCR
        # ==================================================

        ocr_reader = get_ocr_reader()

        results = ocr_reader.readtext(
            filepath
        )

        text = " ".join(
            item[1]
            for item in results
        )


        # ==================================================
        # EXTRACT MEDICINE INFORMATION
        # ==================================================

        batch = extract_batch_number(
            text
        )

        expiry = extract_expiry(
            text
        )

        medicine_name = extract_medicine_name(
            text
        )


        # ==================================================
        # IMAGE QUALITY
        # ==================================================

        image_quality_score, image_issues = (
            analyze_image_quality(
                filepath
            )
        )


        # ==================================================
        # PACKAGING ANALYSIS
        # ==================================================

        packaging_edges = detect_packaging_edges(
            filepath
        )

        (
            packaging_risk,
            packaging_confidence,
            packaging_reasons
        ) = calculate_packaging_risk(
            image_quality_score,
            packaging_edges
        )


        # ==================================================
        # MEDICINE VERIFICATION
        # ==================================================

        verified = verify_medicine(
            medicine_name
        )


        # ==================================================
        # COUNTERFEIT SCORE
        # ==================================================

        (
            data_risk,
            data_confidence,
            reasons
        ) = calculate_counterfeit_score(

            qr_found=code_found,

            batch_found=batch is not None,

            expiry_found=expiry is not None,

            verified=verified is not None
        )


        # ==================================================
        # COMBINED COUNTERFEIT SCORE
        # ==================================================

        combined_risk = round(
            (data_risk * 0.70)
            +
            (packaging_risk * 0.30)
        )

        combined_risk = min(
            max(combined_risk, 0),
            100
        )

        combined_confidence = (
            100 - combined_risk
        )


        # ==================================================
        # COMBINE REASONS
        # ==================================================

        all_reasons = (
            reasons
            + packaging_reasons
            + image_issues
        )


        # ==================================================
        # SAVE SCAN HISTORY
        # ==================================================

        scan = models.MedicineScan(

            user_id=current_user.id,

            medicine_name=medicine_name,

            batch_number=batch,

            qr_verified=code_found,

            packaging_score=packaging_confidence

        )

        db.add(scan)

        db.commit()


        # ==================================================
        # RESPONSE
        # ==================================================

        return {

            "success": True,

            "mode": "MEDICINE",

            "medicine_name": medicine_name,

            "ocr_text": text,

            "code_found": code_found,

            "code_type": code_type,

            "code_value": code_value,

            "batch_number": batch,

            "expiry_date": expiry,

            "database_verified": verified is not None,

            "data_risk": data_risk,

            "data_confidence": data_confidence,

            "packaging_risk": packaging_risk,

            "packaging_confidence": packaging_confidence,

            "combined_counterfeit_risk": combined_risk,

            "combined_confidence": combined_confidence,

            "image_quality_score": image_quality_score,

            "packaging_analysis": {

                "edge_detected":
                    packaging_edges.get(
                        "edge_detected",
                        False
                    ),

                "edge_density":
                    packaging_edges.get(
                        "edge_density",
                        0
                    )

            },

            "reasons": all_reasons
        }


    except HTTPException:
        # Re-raise FastAPI errors without changing them
        raise


    except Exception as e:

        # Rollback database transaction if something
        # goes wrong after db.add()/db.commit()
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Medicine scan failed: {str(e)}"
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