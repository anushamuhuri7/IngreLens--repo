from pydantic import BaseModel, Field
from typing import List, Optional

class UserProfile(BaseModel):
    allergies: List[str] = Field(default_factory=list)
    dietary_flags: List[str] = Field(default_factory=list)
    skin_type: Optional[str] = "Normal"
    is_pregnant: bool = False

class IngredientAnalysis(BaseModel):
    name: str
    risk_level: str  # "Safe", "Caution", "Hazardous"
    hazard_score: int  # 1 to 10 (individual ingredient hazard)
    category: str
    description: str
    allergens_matched: List[str] = []
    side_effects: List[str] = []
    comedogenic_rating: Optional[int] = None

class ScanResult(BaseModel):
    product_name: Optional[str] = "Detected Product"
    safety_score: float  # 0.0 to 10.0 scale
    overall_verdict: str  # "Safe", "Moderate Risk", "Avoid"
    total_ingredients: int
    flagged_count: int
    ingredients: List[IngredientAnalysis]
    summary_ai: str
    recommendations: List[str]