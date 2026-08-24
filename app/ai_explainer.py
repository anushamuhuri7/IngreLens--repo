import httpx
from app.config import settings

async def generate_ai_summary(ingredients_summary: str, verdict: str, safety_score: float) -> str:
    """Generate concise medical summary based on a 0 - 10 scale."""
    if not settings.GEMINI_API_KEY:
        if verdict == "Safe":
            return f"Overall Safety Score is {safety_score}/10. This product features clean, well-tolerated ingredients with minimal known irritants."
        elif verdict == "Moderate Risk":
            return f"Safety Score: {safety_score}/10. Contains moderate sensitizers or potential allergens. Patch testing is recommended."
        else:
            return f"Safety Score: {safety_score}/10. High-risk warning: Flagged hazardous ingredients or personal allergens detected."

    prompt = f"""
    You are an expert toxicologist and dermatologist. Summarize the following product scan:
    - Overall Safety Score: {safety_score}/10
    - Verdict: {verdict}
    - Ingredients: {ingredients_summary}
    Provide a concise 2-sentence plain English summary for a consumer, followed by 2 quick bullet points.
    """
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}",
                json={"contents": [{"parts": [{"text": prompt}]}]}
            )
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return f"Safety rating: {safety_score}/10 ({verdict}). Please review individual flagged items below."