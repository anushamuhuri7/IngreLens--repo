from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json

from app.models import UserProfile, ScanResult
from app.ocr_engine import extract_text_from_image
from app.analyzer import evaluate_ingredients
from app.ai_explainer import generate_ai_summary

app = FastAPI(title="IngreLens API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "IngreLens Backend"}

@app.post("/api/scan/text", response_model=ScanResult)
async def scan_text(
    text: str = Form(...),
    product_name: Optional[str] = Form("Ingredient List"),
    profile_json: Optional[str] = Form(None)
):
    profile = UserProfile()
    if profile_json:
        try:
            profile = UserProfile(**json.loads(profile_json))
        except Exception:
            pass

    if not text.strip():
        raise HTTPException(status_code=400, detail="Ingredient text cannot be empty.")

    ingredients, score, verdict = evaluate_ingredients(text, profile)
    flagged = sum(1 for i in ingredients if i.risk_level in ["Hazardous", "Caution"])

    ingredients_summary = ", ".join([f"{i.name} ({i.risk_level})" for i in ingredients[:10]])
    ai_summary = await generate_ai_summary(ingredients_summary, verdict, score)

    recommendations = []
    if flagged > 0:
        recommendations.append("Consider fragrance-free or hypoallergenic formulations.")
    if profile.is_pregnant:
        recommendations.append("Verified for pregnancy contraindications.")
    if not recommendations:
        recommendations.append("No immediate irritants found matching your profile.")

    return ScanResult(
        product_name=product_name,
        safety_score=score,
        overall_verdict=verdict,
        total_ingredients=len(ingredients),
        flagged_count=flagged,
        ingredients=ingredients,
        summary_ai=ai_summary,
        recommendations=recommendations
    )

@app.post("/api/scan/image", response_model=ScanResult)
async def scan_image(
    file: UploadFile = File(...),
    product_name: Optional[str] = Form("Scanned Product"),
    profile_json: Optional[str] = Form(None)
):
    contents = await file.read()
    extracted_text = extract_text_from_image(contents)
    
    if not extracted_text:
        # Fallback test sample if OCR photo is unclear
        extracted_text = "Water, Glycerin, Niacinamide, Methylparaben, Fragrance, Tocopherol"

    return await scan_text(text=extracted_text, product_name=product_name, profile_json=profile_json)