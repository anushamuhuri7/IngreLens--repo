from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.dependencies import (
    get_db,
    get_current_user
)

from app import models

from app.services.scanner import (
    decode_image,
    detect_food_code,
    resize_for_scanning
)

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
# CONFIGURATION
# ==================================================

MAX_IMAGE_SIZE = (
    10 * 1024 * 1024
)


ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp"
}


# ==================================================
# FOOD SCANNER
# ==================================================

@router.post("/scan")
async def scan_food(

    image: UploadFile = File(...),

    db: Session = Depends(
        get_db
    ),

    current_user: models.User = Depends(
        get_current_user
    )

):

    # ==================================================
    # FILE TYPE
    # ==================================================

    if image.content_type not in (
        ALLOWED_CONTENT_TYPES
    ):

        raise HTTPException(

            status_code=400,

            detail=(
                "Unsupported image format. "
                "Use JPEG, PNG or WEBP."
            )

        )


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
    # IMAGE SIZE
    # ==================================================

    if len(contents) > MAX_IMAGE_SIZE:

        raise HTTPException(

            status_code=413,

            detail=(
                "Image is too large. "
                "Maximum allowed size is 10 MB."
            )

        )


    # ==================================================
    # DECODE IMAGE
    # ==================================================

    frame = decode_image(
        contents
    )


    if frame is None:

        raise HTTPException(

            status_code=400,

            detail="Invalid image file"

        )


    # ==================================================
    # RESIZE
    # ==================================================

    frame = resize_for_scanning(
        frame
    )


    try:

        # ==================================================
        # QR / BARCODE
        # ==================================================

        detected_code = (
            detect_food_code(
                frame
            )
        )


        # ==================================================
        # OCR FALLBACK
        # ==================================================

        if not detected_code:

            try:

                text = (
                    extract_text_from_image(
                        frame
                    )
                )

            except Exception:

                raise HTTPException(

                    status_code=500,

                    detail=(
                        "OCR processing failed."
                    )

                )


            additives = (
                detect_additives(
                    text
                )
            )


            return {

                "success": True,

                "mode": "OCR",

                "ingredients_text":
                    text,

                "detected_additives":
                    additives,

                "message": (
                    "No barcode or QR code "
                    "detected. OCR analysis "
                    "completed."
                )

            }


        # ==================================================
        # CODE
        # ==================================================

        barcode = (
            detected_code["code"]
        )

        scan_type = (
            detected_code["type"]
        )


        # ==================================================
        # OPENFOODFACTS
        # ==================================================

        product = get_product(
            barcode
        )


        if not product:

            return {

                "success": False,

                "mode": scan_type,

                "barcode": barcode,

                "message": (
                    "Code detected, but the "
                    "product was not found "
                    "in OpenFoodFacts."
                )

            }


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

                detail=(
                    "Health profile not found. "
                    "Please create your health "
                    "profile first."
                )

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
        # INGREDIENTS
        # ==================================================

        ingredients = (

            product.get(
                "ingredients_text",
                ""
            )

            or ""

        )


        # ==================================================
        # ADDITIVES
        # ==================================================

        additives = (
            detect_additives(
                ingredients
            )
        )


        # ==================================================
        # AI EXPLANATION
        # ==================================================

        explanation = (
            ai_explanation(
                score,
                warnings,
                additives
            )
        )


        # ==================================================
        # SAVE HISTORY
        # ==================================================

        scan = models.ScanHistory(

            user_id=
                current_user.id,

            product_name=
                product.get(
                    "product_name"
                ),

            safety_score=
                score,

            risk_message=
                ", ".join(
                    warnings
                )

        )


        db.add(
            scan
        )

        db.commit()

        db.refresh(
            scan
        )


        # ==================================================
        # RESPONSE
        # ==================================================

        return {

            "success": True,

            "mode": scan_type,

            "barcode": barcode,

            "product_name":
                product.get(
                    "product_name"
                ),

            "brand":
                product.get(
                    "brands"
                ),

            "ingredients_text":
                product.get(
                    "ingredients_text"
                ),

            "allergens":
                product.get(
                    "allergens"
                ),

            "nutrition_grade":
                product.get(
                    "nutrition_grades"
                ),

            "nova_group":
                product.get(
                    "nova_group"
                ),

            "nutriments":
                product.get(
                    "nutriments",
                    {}
                ),

            "safety_score":
                score,

            "warnings":
                warnings,

            "detected_additives":
                additives,

            "ai_explanation":
                explanation,

            "scan_id":
                scan.id

        }


    except HTTPException:

        raise


    except Exception:

        db.rollback()

        raise HTTPException(

            status_code=500,

            detail=(
                "IngreLens food scan failed. "
                "Please try again."
            )

        )