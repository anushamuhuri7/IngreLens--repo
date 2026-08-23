from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class HealthProfileInput(BaseModel):
    diabetes: bool = False
    hypertension: bool = False
    lactose_intolerant: bool = False
    gluten_allergy: bool = False
    nut_allergy: bool = False


class HealthProfileResponse(HealthProfileInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int


class ScanResponse(BaseModel):
    id: int
    product_name: str | None
    detected_ingredients: list[str]
    safety_score: float
    risk_message: str
    warnings: list[str]
    scanned_at: datetime
