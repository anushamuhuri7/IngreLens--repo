from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app import models
from app.routers import user, profile, food, medicine


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="HealthShield API",
    version="1.0"
)


# Routers
app.include_router(user.router)
app.include_router(profile.router)
app.include_router(food.router)
app.include_router(medicine.router)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://ingre-lens.vercel.app/",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "HealthShield Backend Running"}