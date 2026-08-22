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
import easyocr
import uuid
import os

from pyzbar.pyzbar import decode

from app.dependencies import (
    get_db,
    get_current_user
)

from app import models


# Medicine service functions
from app.services.medicine import (
    extract_batch_number,
    extract_expiry,
    extract_medicine_name,
    verify_medicine,
    calculate_counterfeit_score
)


# Packaging service functions
from app.services.packaging import (
    analyze_image_quality,
    detect_packaging_edges,
    calculate_packaging_risk
)


router = APIRouter(
    prefix="/medicine",
    tags=["Medicine Scanner"]
)


# ---------------------------------------
# EasyOCR
# ---------------------------------------

reader = easyocr.Reader(
    ["en"],
    gpu=False
)


# ---------------------------------------
# Medicine scan endpoint
# ---------------------------------------

@router.post("/scan")
async def scan_medicine(

    image: UploadFile = File(...),

    db: Session = Depends(get_db),

    current_user: models.User = Depends(
        get_current_user
    )
):

    # =====================================
    # 1. Read uploaded image
    # =====================================

    contents = await image.read()

    if not contents:

        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty"
        )


    # =====================================
    # 2. Convert image to OpenCV format
    # =====================================

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


    # =====================================
    # 3. Save image temporarily
    # =====================================

    filename = f"{uuid.uuid4()}.jpg"

    filepath = os.path.join(
        "app",
        "uploads",
        filename
    )

    # Create uploads directory if needed
    os.makedirs(
        os.path.dirname(filepath),
        exist_ok=True
    )

    with open(filepath, "wb") as f:
        f.write(contents)


    try:

        # =================================
        # 4. QR / Barcode detection
        # =================================

        qr_data = decode(frame)

        qr_found = len(qr_data) > 0

        qr_value = None

        if qr_found:

            try:

                qr_value = (
                    qr_data[0]
                    .data
                    .decode("utf-8")
                )

            except UnicodeDecodeError:

                qr_value = str(
                    qr_data[0].data
                )


        # =================================
        # 5. OCR
        # =================================

        results = reader.readtext(
            filepath
        )

        text = " ".join(
            item[1]
            for item in results
        )


        # =================================
        # 6. Extract medicine information
        # =================================

        batch = extract_batch_number(
            text
        )

        expiry = extract_expiry(
            text
        )

        medicine_name = extract_medicine_name(text)
        image_quality_score, image_issues = analyze_image_quality(filepath)

        packaging_edges = detect_packaging_edges(filepath)

        packaging_risk, packaging_confidence, packaging_reasons = (
            calculate_packaging_risk(
                image_quality_score,
                packaging_edges
            )
        )

        # =================================
        # 7. Verify medicine
        # =================================

        verified = verify_medicine(
            medicine_name
        )


        # =================================
        # 8. Calculate data risk
        # =================================

        (
            risk,
            confidence,
            reasons
        ) = calculate_counterfeit_score(

            qr_found=qr_found,

            batch_found=(
                batch is not None
            ),

            expiry_found=(
                expiry is not None
            ),

            verified=(
                verified is not None
            )
        )
        combined_risk = round((risk * 0.7) +(packaging_risk * 0.3))

        combined_confidence = 100 - combined_risk


        # =================================
        # 9. Analyze packaging
        # =================================

        (
            image_quality_score,
            image_issues
        ) = analyze_image_quality(
            filepath
        )


        packaging_edges = (
            detect_packaging_edges(
                filepath
            )
        )


        (
            packaging_risk,
            packaging_confidence,
            packaging_reasons
        ) = calculate_packaging_risk(

            image_quality_score,

            packaging_edges
        )


        # =================================
        # 10. Combine risk scores
        # =================================

        combined_risk = round(
            (risk * 0.70)
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


        # =================================
        # 11. Combine all warnings
        # =================================

        all_reasons = (
            reasons
            +
            packaging_reasons
            +
            image_issues
        )


        # =================================
        # 12. Save scan history
        # =================================

        scan = models.MedicineScan(

            user_id=current_user.id,

            medicine_name=medicine_name,

            batch_number=batch,

            qr_verified=qr_found,

            packaging_score=packaging_confidence
        )

        db.add(scan)

        db.commit()


        # =================================
        # 13. Return result
        # =================================

        return {
    "medicine_name": medicine_name,

    "qr_found": qr_found,
    "qr_value": qr_value,

    "batch_number": batch,
    "expiry_date": expiry,

    "database_verified": verified is not None,

    "data_risk": risk,
    "data_confidence": confidence,

    "packaging_risk": packaging_risk,
    "packaging_confidence": packaging_confidence,

    "combined_counterfeit_risk": combined_risk,
    "combined_confidence": combined_confidence,

    "image_quality_score": image_quality_score,

    "packaging_analysis": {
        "edge_detected": packaging_edges["edge_detected"],
        "edge_density": packaging_edges["edge_density"]
    },

    "reasons": all_reasons
   } 


    finally:

        # =================================
        # 14. Delete temporary image
        # =================================

        if os.path.exists(filepath):

            os.remove(filepath)