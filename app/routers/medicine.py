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

try:
    import easyocr
except Exception:
    easyocr = None

try:
    from pyzbar.pyzbar import decode
except Exception:
    decode = None

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


router = APIRouter(
    prefix="/medicine",
    tags=["Medicine Scanner"]
)


# --------------------------------------------------
# OCR
# --------------------------------------------------

reader = None


def get_ocr_reader():
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


# --------------------------------------------------
# QR / Barcode detection
# --------------------------------------------------

def detect_codes(frame):

    qr_detector = cv2.QRCodeDetector()

    qr_value, points, _ = qr_detector.detectAndDecode(frame)

    if qr_value:
        return True, qr_value, "QR"

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

    return False, None, None


# --------------------------------------------------
# Medicine scan
# --------------------------------------------------

@router.post("/scan")
async def scan_medicine(

    image: UploadFile = File(...),

    db: Session = Depends(get_db),

    current_user: models.User = Depends(
        get_current_user
    )
):

    contents = await image.read()

    if not contents:

        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty"
        )


    # --------------------------------------------------
    # Convert image
    # --------------------------------------------------

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


    # --------------------------------------------------
    # Temporary file
    # --------------------------------------------------

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

        # --------------------------------------------------
        # QR / Barcode
        # --------------------------------------------------

        code_found, code_value, code_type = detect_codes(
            frame
        )


        # --------------------------------------------------
        # OCR
        # --------------------------------------------------

        ocr_reader = get_ocr_reader()

        results = ocr_reader.readtext(
            filepath
        )

        text = " ".join(
            item[1]
            for item in results
        )


        # --------------------------------------------------
        # Extract information
        # --------------------------------------------------

        batch = extract_batch_number(text)

        expiry = extract_expiry(text)

        medicine_name = extract_medicine_name(
            text
        )


        # --------------------------------------------------
        # Image quality
        # --------------------------------------------------

        image_quality_score, image_issues = (
            analyze_image_quality(filepath)
        )


        # --------------------------------------------------
        # Packaging
        # --------------------------------------------------

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


        # --------------------------------------------------
        # Medicine verification
        # --------------------------------------------------

        verified = verify_medicine(
            medicine_name
        )


        # --------------------------------------------------
        # Counterfeit score
        # --------------------------------------------------

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


        # --------------------------------------------------
        # Combined score
        # --------------------------------------------------

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


        # --------------------------------------------------
        # Reasons
        # --------------------------------------------------

        all_reasons = (
            reasons
            + packaging_reasons
            + image_issues
        )


        # --------------------------------------------------
        # Save history
        # --------------------------------------------------

        scan = models.MedicineScan(

            user_id=current_user.id,

            medicine_name=medicine_name,

            batch_number=batch,

            qr_verified=code_found,

            packaging_score=packaging_confidence

        )

        db.add(scan)

        db.commit()


        # --------------------------------------------------
        # Response
        # --------------------------------------------------

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
                    packaging_edges["edge_detected"],

                "edge_density":
                    packaging_edges["edge_density"]

            },

            "reasons": all_reasons
        }


    finally:

        if os.path.exists(filepath):

            os.remove(filepath)