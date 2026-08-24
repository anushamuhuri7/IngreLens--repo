"""IngreLens FastAPI backend — MongoDB + Claude Sonnet 5 label analysis."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import bcrypt
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

# Load env from /app/backend/.env explicitly (supervisor cwd is /app)
load_dotenv(Path(__file__).resolve().parent.parent / "backend" / ".env")
load_dotenv()  # also picks up default cwd .env if present

from app.ai_analyzer import analyze_label  # noqa: E402
from app.barcode_service import lookup_barcode  # noqa: E402
from app.ocr_engine import extract_text_from_image  # noqa: E402

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
SECRET = os.environ.get("SECRET_KEY", "ingrelens-local-secret")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
users_col = db["users"]
profiles_col = db["profiles"]
scans_col = db["scans"]
attempts_col = db["login_attempts"]

app = FastAPI(title="IngreLens API", version="3.0.0")


@app.on_event("startup")
async def _ensure_indexes():
    await users_col.create_index("email", unique=True)
    await users_col.create_index("id", unique=True)
    await scans_col.create_index([("user_id", 1), ("created_at", -1)])
    await profiles_col.create_index("user_id", unique=True)

origins_raw = os.getenv("CORS_ORIGINS", "*")
allow_origins = ["*"] if origins_raw.strip() == "*" else [o.strip() for o in origins_raw.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- helpers ----------
def new_id() -> str:
    return uuid.uuid4().hex


def make_token(user_id: str) -> str:
    raw = user_id.encode()
    signature = hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(raw + b":" + signature.encode()).decode()


async def current_user(authorization: str | None) -> dict[str, Any]:
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

    user = await users_col.find_one({"id": user_id}, {"password": 0, "_id": 0})
    if not user:
        raise HTTPException(401, "User not found")
    return user


def hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_pw(password: str, stored: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), stored.encode())
    except ValueError:
        return False


DEFAULT_PROFILE: dict[str, Any] = {
    "goals": [],
    "allergies": [],
    "conditions": [],
    "medicines": [],
    "age": "",
    "avatar": "",
}


async def get_profile(user_id: str) -> dict[str, Any]:
    profile = await profiles_col.find_one({"user_id": user_id}, {"_id": 0, "user_id": 0})
    return profile or dict(DEFAULT_PROFILE)


# ---------- schemas ----------
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
    avatar: str = ""  # data-URL (image/*), client-downscaled to <150KB


MAX_AVATAR_BYTES = 250_000  # ~250KB data-URL cap


# ---------- routes ----------
@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "IngreLens Backend", "db": DB_NAME}


@app.post("/api/auth/register")
async def register(payload: Credentials):
    email = payload.email.lower().strip()
    existing = await users_col.find_one({"email": email})
    if existing:
        raise HTTPException(409, "An account with this email already exists")
    user_id = new_id()
    doc = {
        "id": user_id,
        "name": payload.name.strip() or "IngreLens member",
        "email": email,
        "password": hash_pw(payload.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await users_col.insert_one(doc)
    return {
        "user": {"id": user_id, "name": doc["name"], "email": email},
        "token": make_token(user_id),
    }


@app.post("/api/auth/login")
async def login(payload: Credentials):
    email = payload.email.lower().strip()
    attempt_key = f"login:{email}"
    attempt = await attempts_col.find_one({"key": attempt_key}) or {"count": 0, "until": 0}
    if attempt.get("until", 0) > time.time():
        raise HTTPException(429, "Too many attempts. Try again in a few minutes.")

    user = await users_col.find_one({"email": email})
    if not user or not check_pw(payload.password, user.get("password", "")):
        count = attempt.get("count", 0) + 1
        until = time.time() + 900 if count >= 5 else 0
        await attempts_col.update_one(
            {"key": attempt_key},
            {"$set": {"key": attempt_key, "count": 0 if until else count, "until": until}},
            upsert=True,
        )
        raise HTTPException(401, "Invalid email or password")

    await attempts_col.delete_one({"key": attempt_key})
    return {
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
        "token": make_token(user["id"]),
    }


@app.get("/api/auth/me")
async def me(authorization: str | None = Header(None)):
    user = await current_user(authorization)
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


@app.get("/api/profile")
async def read_profile(authorization: str | None = Header(None)):
    user = await current_user(authorization)
    return await get_profile(user["id"])


@app.put("/api/profile")
async def save_profile(payload: ProfilePayload, authorization: str | None = Header(None)):
    user = await current_user(authorization)
    # Merge semantics: only update fields the client explicitly sent — avoids
    # wiping the avatar (or any other field) when the client PUTs a partial body.
    data = payload.model_dump(exclude_unset=True)
    if "avatar" in data:
        avatar = data["avatar"] or ""
        if avatar and not avatar.startswith("data:image/"):
            raise HTTPException(400, "Avatar must be an image data URL")
        if len(avatar) > MAX_AVATAR_BYTES:
            raise HTTPException(413, "Avatar image is too large — please crop or use a smaller photo")
    await profiles_col.update_one(
        {"user_id": user["id"]},
        {"$set": {**data, "user_id": user["id"], "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return await get_profile(user["id"])


@app.post("/api/scan")
async def scan_label(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    product_name: str = Form("Scanned label"),
    mode: str = Form("FOOD"),
    barcode: str | None = Form(None),
    authorization: str | None = Header(None),
):
    user = await current_user(authorization)
    mode_upper = (mode or "FOOD").upper()
    if mode_upper not in {"FOOD", "MEDICINE"}:
        mode_upper = "FOOD"

    captured = (text or "").strip()
    effective_name = product_name
    barcode_meta: dict[str, Any] | None = None
    barcode_missed = False

    if barcode:
        barcode_meta = await lookup_barcode(barcode.strip(), mode_upper)
        if barcode_meta:
            mode_upper = barcode_meta.get("kind", mode_upper)
            if not effective_name or effective_name == "Scanned label":
                effective_name = barcode_meta.get("product_name") or effective_name
            packed = barcode_meta.get("packed_text", "")
            captured = f"{packed}\n{captured}".strip() if captured else packed
        else:
            barcode_missed = True

    if file:
        contents = await file.read()
        ocr_text = extract_text_from_image(contents)
        if ocr_text:
            captured = ocr_text if not captured else f"{captured}\n{ocr_text}"

    if not captured:
        if barcode_missed:
            raise HTTPException(404, f"We couldn't find barcode {barcode} in the open catalog. Try capturing the label instead.")
        raise HTTPException(400, "Add a label photo, barcode or paste the label text first")

    profile = await get_profile(user["id"])
    result = await analyze_label(
        extracted_text=captured,
        profile=profile,
        mode=mode_upper,
        product_name=effective_name,
    )
    if barcode_meta:
        result["barcode"] = {
            "code": barcode.strip(),
            "source": barcode_meta.get("source"),
            "brand": barcode_meta.get("brand"),
            "image_url": barcode_meta.get("image_url"),
        }

    scan_id = new_id()
    stored = {
        **result,
        "id": scan_id,
        "user_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await scans_col.insert_one(stored)
    stored.pop("_id", None)
    return stored


@app.get("/api/barcode/{code}")
async def barcode_lookup(code: str, mode: str = "AUTO", authorization: str | None = Header(None)):
    await current_user(authorization)
    result = await lookup_barcode(code, mode)
    if not result:
        raise HTTPException(404, "We couldn't find this barcode in the open catalog.")
    return result


@app.get("/api/history")
async def history(authorization: str | None = Header(None)):
    user = await current_user(authorization)
    cursor = scans_col.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).limit(200)
    return [doc async for doc in cursor]


@app.delete("/api/history")
async def clear_history(authorization: str | None = Header(None)):
    user = await current_user(authorization)
    result = await scans_col.delete_many({"user_id": user["id"]})
    return {"cleared": True, "removed": result.deleted_count}
