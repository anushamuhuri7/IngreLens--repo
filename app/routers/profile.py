from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.dependencies import get_current_user, get_db

router = APIRouter(prefix="/profile", tags=["profile"])


@router.put("/", response_model=schemas.HealthProfileResponse)
def upsert_profile(payload: schemas.HealthProfileInput, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    profile = db.query(models.HealthProfile).filter_by(user_id=current_user.id).first()
    if profile is None:
        profile = models.HealthProfile(user_id=current_user.id)
        db.add(profile)
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/", response_model=schemas.HealthProfileResponse)
def create_or_update_profile(payload: schemas.HealthProfileInput, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return upsert_profile(payload, db, current_user)


@router.get("/me", response_model=schemas.HealthProfileResponse | None)
def get_profile(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.HealthProfile).filter_by(user_id=current_user.id).first()
