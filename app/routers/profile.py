from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.dependencies import get_db, get_current_user

router = APIRouter(
    prefix="/profile",
    tags=["Health Profile"]
)


@router.post("/", response_model=schemas.HealthProfileResponse)
def create_profile(
    profile: schemas.HealthProfileCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    existing = db.query(models.HealthProfile).filter(
        models.HealthProfile.user_id == current_user.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Profile already exists"
        )

    new_profile = models.HealthProfile(
        user_id=current_user.id,
        diabetes=profile.diabetes,
        hypertension=profile.hypertension,
        lactose_intolerant=profile.lactose_intolerant,
        gluten_allergy=profile.gluten_allergy,
        nut_allergy=profile.nut_allergy
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return new_profile


@router.get("/me", response_model=schemas.HealthProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    profile = db.query(models.HealthProfile).filter(
        models.HealthProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )

    return profile


@router.put("/me", response_model=schemas.HealthProfileResponse)
def update_profile(
    profile: schemas.HealthProfileCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    db_profile = db.query(models.HealthProfile).filter(
        models.HealthProfile.user_id == current_user.id
    ).first()

    if not db_profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )

    db_profile.diabetes = profile.diabetes
    db_profile.hypertension = profile.hypertension
    db_profile.lactose_intolerant = profile.lactose_intolerant
    db_profile.gluten_allergy = profile.gluten_allergy
    db_profile.nut_allergy = profile.nut_allergy

    db.commit()
    db.refresh(db_profile)

    return db_profile