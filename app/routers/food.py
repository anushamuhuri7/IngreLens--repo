from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models, schemas
from app.dependencies import get_current_user, get_db
from app.services.rating import compute_rating, split_ingredients
from app.services.scanner import ALLOWED_CONTENT_TYPES, scan_image, validate_image

router = APIRouter(prefix="/food", tags=["food scanner"])


@router.post("/scan", response_model=schemas.ScanResponse)
async def scan_food(
    image: UploadFile = File(...),
    product_name: str | None = Form(None),
    ingredients: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Use a JPEG, PNG, or WEBP image")
    contents = await image.read()
    try:
        validate_image(contents)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    scanned_name, scanned_ingredients = scan_image(contents)
    detected_ingredients = split_ingredients(ingredients) if ingredients else scanned_ingredients
    if not detected_ingredients:
        raise HTTPException(status_code=422, detail="No ingredients found. Supply the ingredients form field after scanning the package label.")

    profile = db.query(models.HealthProfile).filter_by(user_id=current_user.id).first()
    score, warnings = compute_rating(detected_ingredients, profile)
    record = models.ScanHistory(
        user_id=current_user.id,
        product_name=product_name or scanned_name,
        detected_ingredients=", ".join(detected_ingredients),
        safety_score=score,
        risk_message="; ".join(warnings),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return schemas.ScanResponse(id=record.id, product_name=record.product_name, detected_ingredients=detected_ingredients, safety_score=score, risk_message=record.risk_message, warnings=warnings, scanned_at=record.scanned_at)


@router.get("/history", response_model=list[schemas.ScanResponse])
def scan_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    records = db.query(models.ScanHistory).filter_by(user_id=current_user.id).order_by(models.ScanHistory.scanned_at.desc()).all()
    return [schemas.ScanResponse(id=item.id, product_name=item.product_name, detected_ingredients=split_ingredients(item.detected_ingredients), safety_score=item.safety_score, risk_message=item.risk_message, warnings=item.risk_message.split("; "), scanned_at=item.scanned_at) for item in records]


@router.delete("/history", status_code=204)
def clear_scan_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db.query(models.ScanHistory).filter_by(user_id=current_user.id).delete()
    db.commit()
