from fastapi import FastAPI
from app.database import Base, engine
from app import models
from app.routers import user
from app.routers import user, profile
from app.routers import user, profile, food
from app.routers import user, profile, food, medicine
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HealthShield API",
    version="1.0"
)
app.include_router(user.router)
app.include_router(user.router)
app.include_router(profile.router)
app.include_router(food.router)
app.include_router(medicine.router)

@app.get("/")
def root():
    return {"message": "HealthShield Backend Running"}