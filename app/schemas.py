from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True


class HealthProfileCreate(BaseModel):
    diabetes: bool = False
    hypertension: bool = False
    lactose_intolerant: bool = False
    gluten_allergy: bool = False
    nut_allergy: bool = False


class HealthProfileResponse(HealthProfileCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str