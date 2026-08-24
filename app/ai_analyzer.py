"""Claude Sonnet 5 powered label analyzer for IngreLens.

Sends OCR-extracted label text + user profile to the model and expects a
structured JSON verdict. Falls back gracefully on transport/parse errors so
the scan endpoint never breaks the UX.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from typing import Any

import httpx

EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

SYSTEM_PROMPT = """You are IngreLens, an AI health analyst that reviews food and medicine labels for individuals.

You will receive:
1. The OCR-extracted text of a label (may be noisy)
2. The user's health profile (allergies, medical conditions, current medicines, health goals, age)
3. Whether it is a FOOD or MEDICINE label

Return ONLY a valid JSON object (no markdown, no prose, no code fences) with this exact schema:
{
  "product_name": string,           // best guess of the product, or "Scanned label"
  "safety_score": number,           // 0.0-10.0 where 10 = safest for THIS user
  "overall_verdict": string,        // one of: "Safe", "Moderate Risk", "Personal caution", "Avoid"
  "total_ingredients": integer,
  "flagged_count": integer,
  "ingredients": [
    {
      "name": string,
      "risk_level": string,         // "Safe" | "Caution" | "Hazardous"
      "hazard_score": integer,      // 1-10
      "category": string,           // short category e.g. "Preservative", "Sweetener", "Active ingredient"
      "description": string,        // 1-2 sentences, plain language
      "side_effects": [string]
    }
  ],
  "profile_match": [string],        // items from the user's allergies/conditions/medicines that appear in this label
  "summary_ai": string,             // 2-3 sentence personalised summary that references the user's profile
  "recommendations": [string],      // 2-4 actionable tips tailored to this user
  "medicine_notice": string         // only for MEDICINE labels; empty string for food
}

Rules:
- Personalise the verdict using the user's profile. If ANY allergy, condition, or medicine conflicts with an ingredient, mark that ingredient Hazardous and lower the safety score to <=5.
- Never diagnose or prescribe. For medicine labels, always add a medicine_notice reminding the user to confirm dosage, expiry and interactions with a pharmacist.
- If OCR text is empty or unreadable, return safety_score 0 with overall_verdict "Avoid" and explain in summary_ai.
- Output must parse with json.loads. Do not wrap in ``` fences.
"""


def _fallback(mode: str, extracted_text: str, message: str) -> dict[str, Any]:
    return {
        "product_name": "Scanned label",
        "safety_score": 0.0,
        "overall_verdict": "Avoid",
        "total_ingredients": 0,
        "flagged_count": 0,
        "ingredients": [],
        "profile_match": [],
        "summary_ai": message,
        "recommendations": ["Retake a clearer photo of the label", "Ensure the ingredients list is inside the guide"],
        "medicine_notice": "Consult a pharmacist for medicine details." if mode == "MEDICINE" else "",
        "extracted_text": extracted_text,
        "type": mode,
    }


def _extract_json(raw: str) -> dict[str, Any] | None:
    if not raw:
        return None
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


def _shape(payload: dict[str, Any], mode: str, extracted_text: str, product_name: str) -> dict[str, Any]:
    ingredients = payload.get("ingredients") or []
    safe_ingredients = []
    for item in ingredients:
        if not isinstance(item, dict):
            continue
        safe_ingredients.append({
            "name": str(item.get("name", "Ingredient"))[:120],
            "risk_level": item.get("risk_level", "Safe") if item.get("risk_level") in {"Safe", "Caution", "Hazardous"} else "Safe",
            "hazard_score": int(item.get("hazard_score", 1) or 1),
            "category": str(item.get("category", "Ingredient"))[:80],
            "description": str(item.get("description", ""))[:400],
            "side_effects": [str(s)[:120] for s in (item.get("side_effects") or []) if s],
        })
    try:
        score = float(payload.get("safety_score", 0))
    except (TypeError, ValueError):
        score = 0.0
    score = max(0.0, min(10.0, round(score, 1)))
    verdict = str(payload.get("overall_verdict", "Moderate Risk"))
    return {
        "product_name": str(payload.get("product_name") or product_name or "Scanned label")[:120],
        "safety_score": score,
        "overall_verdict": verdict,
        "total_ingredients": int(payload.get("total_ingredients") or len(safe_ingredients)),
        "flagged_count": int(payload.get("flagged_count") or sum(1 for i in safe_ingredients if i["risk_level"] != "Safe")),
        "ingredients": safe_ingredients,
        "profile_match": [str(p) for p in (payload.get("profile_match") or []) if p],
        "summary_ai": str(payload.get("summary_ai") or "")[:800],
        "recommendations": [str(r)[:200] for r in (payload.get("recommendations") or []) if r][:6],
        "medicine_notice": str(payload.get("medicine_notice") or "") if mode == "MEDICINE" else "",
        "extracted_text": extracted_text,
        "type": mode,
    }


async def _call_gemini(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 16384,
            "responseMimeType": "application/json",
        },
    }
    async with httpx.AsyncClient(timeout=55.0) as client:
        response = await client.post(
            url,
            headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
            json=payload,
        )
    response.raise_for_status()
    body = response.json()
    parts = body["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts)


async def _call_claude(prompt: str) -> str:
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"ingrelens-{uuid.uuid4().hex[:12]}",
        system_message=SYSTEM_PROMPT,
    ).with_model("anthropic", "claude-sonnet-5")
    reply = await chat.send_message(UserMessage(text=prompt))
    return reply if isinstance(reply, str) else str(reply)


async def analyze_label(
    *,
    extracted_text: str,
    profile: dict[str, Any],
    mode: str,
    product_name: str,
) -> dict[str, Any]:
    if not (GEMINI_API_KEY or EMERGENT_LLM_KEY):
        return _fallback(mode, extracted_text, "AI service is not configured. Ask an administrator to set GEMINI_API_KEY.")
    if not extracted_text or not extracted_text.strip():
        return _fallback(mode, extracted_text, "We couldn't read the label. Please retake with better lighting.")

    profile_summary = {
        "age": profile.get("age", ""),
        "health_goals": profile.get("goals", []),
        "allergies_and_conditions": profile.get("allergies", []) + profile.get("conditions", []),
        "current_medicines": profile.get("medicines", []),
    }
    prompt = (
        f"Label type: {mode}\n"
        f"Suggested product name: {product_name or 'unknown'}\n"
        f"User profile: {json.dumps(profile_summary, ensure_ascii=False)}\n"
        f"OCR text from the label:\n\"\"\"\n{extracted_text.strip()[:4000]}\n\"\"\"\n\n"
        f"Return the JSON report now."
    )

    try:
        reply = await (_call_gemini(prompt) if GEMINI_API_KEY else _call_claude(prompt))
    except Exception as exc:  # noqa: BLE001
        return _fallback(mode, extracted_text, f"AI analysis is temporarily unavailable ({exc.__class__.__name__}). Please retry in a moment.")

    payload = _extract_json(reply)
    if not payload:
        return _fallback(mode, extracted_text, "AI returned an unreadable response. Please retry the scan.")
    return _shape(payload, mode, extracted_text, product_name)
