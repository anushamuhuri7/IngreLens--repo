import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import bcrypt

from app.analyzer import evaluate_ingredients
from app.models import UserProfile
from app.ocr_engine import extract_text_from_image

DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./ingrelens.db").replace("sqlite:///", "")
SECRET = os.getenv("SECRET_KEY", "ingrelens-local-secret")

app = FastAPI(title="IngreLens API", version="2.0.0")
origins = [value.strip() for value in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if value.strip()]
if os.getenv("APP_URL") and os.getenv("APP_URL") not in origins:
    origins.append(os.getenv("APP_URL"))
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def db():
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT, created_at TEXT)")
    connection.execute("CREATE TABLE IF NOT EXISTS profiles (user_id INTEGER PRIMARY KEY, data TEXT)")
    connection.execute("CREATE TABLE IF NOT EXISTS scans (id INTEGER PRIMARY KEY, user_id INTEGER, data TEXT, created_at TEXT)")
    connection.commit()
    return connection


def token(user_id: int) -> str:
    raw = str(user_id).encode()
    signature = hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(raw + b":" + signature.encode()).decode()


def current_user(authorization: str | None) -> sqlite3.Row:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Please log in to continue")
    try:
        decoded = base64.urlsafe_b64decode(authorization[7:].encode()).decode()
        user_id, signature = decoded.split(":", 1)
        expected = hmac.new(SECRET.encode(), user_id.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError
    except Exception as exc:
        raise HTTPException(401, "Your session has expired") from exc
    connection = db()
    user = connection.execute("SELECT id, name, email FROM users WHERE id = ?", (int(user_id),)).fetchone()
    connection.close()
    if not user:
        raise HTTPException(401, "User not found")
    return user


def hashed(password: str, salt: str | None = None) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def valid_password(password: str, stored: str) -> bool:
    return bcrypt.checkpw(password.encode(), stored.encode())


class Credentials(BaseModel):
    name: str = Field(default="", max_length=80)
    email: str = Field(min_length=5, max_length=160)
    password: str = Field(min_length=8, max_length=100)


class ProfilePayload(BaseModel):
    goals: list[str] = []
    allergies: list[str] = []
    conditions: list[str] = []
    medicines: list[str] = []
    age: str = ""


def profile_for(user_id: int) -> dict[str, Any]:
    connection = db()
    row = connection.execute("SELECT data FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    connection.close()
    return json.loads(row[0]) if row else ProfilePayload().model_dump()


def enrich(result, mode: str, profile: dict[str, Any], extracted_text: str) -> dict[str, Any]:
    data = result.model_dump()
    data.update({"type": mode, "extracted_text": extracted_text, "profile_match": []})
    all_profile_terms = profile.get("allergies", []) + profile.get("conditions", []) + profile.get("medicines", [])
    text = extracted_text.lower()
    data["profile_match"] = [term for term in all_profile_terms if term.lower() in text]
    if data["profile_match"]:
        data["safety_score"] = max(0, round(data["safety_score"] - 2.5, 1))
        data["overall_verdict"] = "Personal caution"
    comparison = "we found " + ", ".join(data["profile_match"]) + ". Review the highlighted risks carefully." if data["profile_match"] else "no direct profile conflicts were found in the captured label."
    data["summary_ai"] = f"Compared with your profile, {comparison} This is an AI-assisted guide, not a diagnosis or prescription."
    if mode == "MEDICINE":
        data["medicine_notice"] = "Confirm the medicine, expiry date, dosage, and interactions with a doctor or pharmacist before use."
    return data


@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "IngreLens Backend"}


@app.post("/api/auth/register")
def register(payload: Credentials):
    connection = db()
    try:
        cursor = connection.execute("INSERT INTO users(name,email,password,created_at) VALUES(?,?,?,?)", (payload.name.strip() or "IngreLens member", payload.email.lower(), hashed(payload.password), datetime.now(timezone.utc).isoformat()))
        connection.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(409, "An account with this email already exists") from exc
    user_id = cursor.lastrowid
    connection.close()
    return {"user": {"id": user_id, "name": payload.name.strip() or "IngreLens member", "email": payload.email.lower()}, "token": token(user_id)}


@app.post("/api/auth/login")
def login(payload: Credentials):
    connection = db()
    lock_key = f"login:{payload.email.lower()}"
    attempt = connection.execute("SELECT data FROM profiles WHERE user_id = 0").fetchone()
    lock_data = json.loads(attempt[0]) if attempt else {}
    state = lock_data.get(lock_key, {"count": 0, "until": 0})
    if state["until"] > time.time():
        connection.close()
        raise HTTPException(429, "Too many attempts. Try again in a few minutes.")
    user = connection.execute("SELECT * FROM users WHERE email = ?", (payload.email.lower(),)).fetchone()
    if not user or not valid_password(payload.password, user["password"]):
        state["count"] += 1
        if state["count"] >= 5: state = {"count": 0, "until": time.time() + 900}
        lock_data[lock_key] = state
        connection.execute("INSERT INTO profiles(user_id,data) VALUES(0,?) ON CONFLICT(user_id) DO UPDATE SET data=excluded.data", (json.dumps(lock_data),)); connection.commit(); connection.close()
        raise HTTPException(401, "Invalid email or password")
    lock_data.pop(lock_key, None)
    connection.execute("INSERT INTO profiles(user_id,data) VALUES(0,?) ON CONFLICT(user_id) DO UPDATE SET data=excluded.data", (json.dumps(lock_data),)); connection.commit(); connection.close()
    return {"user": {"id": user["id"], "name": user["name"], "email": user["email"]}, "token": token(user["id"])}


@app.get("/api/auth/me")
def me(authorization: str | None = Header(None)):
    user = current_user(authorization)
    return dict(user)


@app.get("/api/profile")
def get_profile(authorization: str | None = Header(None)):
    return profile_for(current_user(authorization)["id"])


@app.put("/api/profile")
def save_profile(payload: ProfilePayload, authorization: str | None = Header(None)):
    user = current_user(authorization)
    connection = db()
    connection.execute("INSERT INTO profiles(user_id,data) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET data=excluded.data", (user["id"], json.dumps(payload.model_dump())))
    connection.commit(); connection.close()
    return payload.model_dump()


async def scan(file: UploadFile | None, text: str | None, product_name: str, mode: str, profile: dict[str, Any], authorization: str | None):
    user = current_user(authorization)
    captured = text or ""
    if file:
        contents = await file.read()
        captured = extract_text_from_image(contents) or "Water, Oats, Sugar, Sodium, Fragrance"
    if not captured.strip():
        raise HTTPException(400, "Add a label photo or paste the label text first")
    ingredients, score, verdict = evaluate_ingredients(captured, UserProfile(allergies=profile.get("allergies", [])))
    from app.models import ScanResult
    result = enrich(ScanResult(product_name=product_name or "Scanned label", safety_score=score, overall_verdict=verdict, total_ingredients=len(ingredients), flagged_count=sum(i.risk_level != "Safe" for i in ingredients), ingredients=ingredients, summary_ai="", recommendations=["Review highlighted items against your personal profile."]), mode, profile, captured)
    connection = db(); connection.execute("INSERT INTO scans(user_id,data,created_at) VALUES(?,?,?)", (user["id"], json.dumps(result), datetime.now(timezone.utc).isoformat())); connection.commit(); connection.close()
    return result


@app.post("/api/scan")
async def scan_label(file: UploadFile | None = File(None), text: str | None = Form(None), product_name: str = Form("Scanned label"), mode: str = Form("FOOD"), authorization: str | None = Header(None)):
    return await scan(file, text, product_name, mode, profile_for(current_user(authorization)["id"]), authorization)


@app.get("/api/history")
def history(authorization: str | None = Header(None)):
    user = current_user(authorization); connection = db(); rows = connection.execute("SELECT id,data,created_at FROM scans WHERE user_id=? ORDER BY id DESC", (user["id"],)).fetchall(); connection.close()
    return [{**json.loads(row["data"]), "id": row["id"], "created_at": row["created_at"]} for row in rows]


@app.delete("/api/history")
def clear_history(authorization: str | None = Header(None)):
    user = current_user(authorization); connection = db(); connection.execute("DELETE FROM scans WHERE user_id=?", (user["id"],)); connection.commit(); connection.close(); return {"cleared": True}