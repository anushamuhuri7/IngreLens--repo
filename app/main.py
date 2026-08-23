import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401 - imports model metadata before table creation
from app.database import Base, engine
from app.routers import food, profile, user

Base.metadata.create_all(bind=engine)

app = FastAPI(title="IngreLens API", version="1.0.0")
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(user.router)
app.include_router(profile.router)
app.include_router(food.router)


@app.get("/")
def health_check():
    return {"message": "IngreLens API is running"}
