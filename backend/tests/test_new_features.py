"""IngreLens iteration-3 features: real OCR, barcode lookup, profile avatar."""
from __future__ import annotations

import io
import os
import re
import sys
import uuid
from pathlib import Path

# The FastAPI app package lives at /app/app; pytest rootdir is /app/backend so
# make the repo root importable for the direct-OCR unit test.
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

import pytest
import requests
from dotenv import dotenv_values
from PIL import Image, ImageDraw, ImageFont

frontend_env = dotenv_values("/app/frontend/.env") if Path("/app/frontend/.env").exists() else {}
base_url = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or frontend_env.get("REACT_APP_BACKEND_URL")
    or "https://cb5958a8-61bb-453d-9313-bce9a37c4b1e.preview.emergentagent.com"
)
BASE_URL = base_url.rstrip("/")
API = f"{BASE_URL}/api"
LLM_TIMEOUT = 150

NUTELLA = "3017620422003"
# NOTE: 9999999999999 exists in OpenFoodFacts as a test product ("Salatgurke"),
# so it cannot be used to assert the 404 path. 7777777777770 is genuinely unknown.
UNKNOWN_BARCODE = "7777777777770"
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]
FONT_PATH = next((p for p in FONT_CANDIDATES if Path(p).exists()), None)


def rand_email(tag: str = "user") -> str:
    return f"TEST_{tag}_{uuid.uuid4().hex[:10]}@ingrelens.test"


@pytest.fixture(scope="module")
def api_client():
    return requests.Session()


@pytest.fixture(scope="module")
def seeded_credentials():
    path = Path("/app/memory/test_credentials.md")
    if not path.exists():
        pytest.skip("Missing /app/memory/test_credentials.md")
    content = path.read_text(encoding="utf-8")
    email = re.search(r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?email(?:\*\*)?\s*:\s*`?([^`\s]+)", content)
    password = re.search(r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?password(?:\*\*)?\s*:\s*`?([^`\s]+)", content)
    if not email or not password:
        pytest.skip("No email/password found in test_credentials.md")
    return {"email": email.group(1), "password": password.group(1)}


@pytest.fixture(scope="module")
def seeded_headers(api_client, seeded_credentials):
    r = api_client.post(f"{API}/auth/login", json=seeded_credentials, timeout=30)
    if r.status_code != 200:
        reg = api_client.post(
            f"{API}/auth/register",
            json={"name": "IngreLens QA", **seeded_credentials},
            timeout=30,
        )
        if reg.status_code != 200:
            pytest.fail(f"cannot authenticate seeded account: login={r.status_code} register={reg.status_code}")
        return {"Authorization": f"Bearer {reg.json()['token']}"}
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture(scope="module")
def temp_headers(api_client):
    """Throwaway user so seeded account data is not polluted."""
    email = rand_email("feat")
    r = api_client.post(
        f"{API}/auth/register",
        json={"name": "TEST Feature User", "email": email, "password": "Password123!"},
        timeout=30,
    )
    assert r.status_code == 200, r.text[:300]
    return {"Authorization": f"Bearer {r.json()['token']}"}


def label_image_bytes() -> bytes:
    if not FONT_PATH:
        pytest.skip("No TrueType font available to render the OCR fixture image")
    img = Image.new("RGB", (900, 400), "white")
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 34)
    d.text((30, 40), "INGREDIENTS:", fill="black", font=font)
    d.text((30, 120), "Wheat flour, Sugar, Salt,", fill="black", font=font)
    d.text((30, 180), "Peanut oil, Sodium benzoate", fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


# ---------- health regression ----------
def test_health(api_client):
    r = api_client.get(f"{API}/health", timeout=30)
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


# ---------- OCR ----------
class TestOCR:
    def test_ocr_engine_direct(self):
        from app.ocr_engine import extract_text_from_image

        text = extract_text_from_image(label_image_bytes()).lower()
        assert any(w in text for w in ("flour", "sugar", "salt")), f"OCR returned: {text!r}"

    def test_scan_with_image_returns_real_analysis(self, api_client, temp_headers):
        files = {"file": ("label.png", label_image_bytes(), "image/png")}
        r = api_client.post(
            f"{API}/scan",
            files=files,
            data={"mode": "FOOD", "product_name": "TEST OCR Snack"},
            headers=temp_headers,
            timeout=LLM_TIMEOUT,
        )
        assert r.status_code == 200, r.text[:500]
        d = r.json()
        extracted = d["extracted_text"].lower()
        assert any(w in extracted for w in ("flour", "sugar", "salt")), f"extracted_text={d['extracted_text']!r}"
        assert int(d["total_ingredients"]) > 0, d
        assert "ai service" not in d["summary_ai"].lower(), d["summary_ai"]
        assert "temporarily unavailable" not in d["summary_ai"].lower()
        assert isinstance(d["ingredients"], list) and d["ingredients"]
        assert d["type"] == "FOOD"


# ---------- barcode lookup ----------
class TestBarcode:
    def test_barcode_requires_auth(self, api_client):
        r = api_client.get(f"{API}/barcode/{NUTELLA}?mode=FOOD", timeout=30)
        assert r.status_code == 401, r.text[:300]

    def test_barcode_food_lookup(self, api_client, seeded_headers):
        r = api_client.get(f"{API}/barcode/{NUTELLA}?mode=FOOD", headers=seeded_headers, timeout=40)
        assert r.status_code == 200, r.text[:500]
        d = r.json()
        assert d["source"] == "openfoodfacts"
        assert d["kind"] == "FOOD"
        assert "nutella" in d["product_name"].lower(), d["product_name"]
        assert d["packed_text"].strip()
        assert "_id" not in d

    def test_barcode_unknown_404(self, api_client, seeded_headers):
        r = api_client.get(f"{API}/barcode/{UNKNOWN_BARCODE}?mode=FOOD", headers=seeded_headers, timeout=40)
        assert r.status_code == 404, r.text[:300]
        assert r.json().get("detail", "").strip()

    def test_barcode_medicine_lookup_openfda(self, api_client, seeded_headers):
        """product_ndc style code resolves through OpenFDA."""
        probe = api_client.get("https://api.fda.gov/drug/ndc.json?limit=1", timeout=30)
        if probe.status_code != 200 or not probe.json().get("results"):
            pytest.skip("OpenFDA unavailable")
        ndc = probe.json()["results"][0]["product_ndc"]
        r = api_client.get(f"{API}/barcode/{ndc}?mode=MEDICINE", headers=seeded_headers, timeout=40)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d["source"] == "openfda"
        assert d["kind"] == "MEDICINE"
        assert d["product_name"].strip()
        assert d["packed_text"].strip()

    def test_scan_with_unknown_barcode_and_no_text_400(self, api_client, temp_headers):
        r = api_client.post(
            f"{API}/scan", data={"barcode": UNKNOWN_BARCODE}, headers=temp_headers, timeout=60
        )
        # Iteration 4: backend now answers 404 with an explicit barcode-not-found
        # message (previously a generic 400) — both are acceptable client errors.
        assert r.status_code in (400, 404), r.text[:300]
        assert UNKNOWN_BARCODE in r.json()["detail"] or "barcode" in r.json()["detail"].lower()

    def test_scan_via_barcode_only(self, api_client, temp_headers):
        r = api_client.post(
            f"{API}/scan",
            data={"barcode": NUTELLA},
            headers=temp_headers,
            timeout=LLM_TIMEOUT,
        )
        assert r.status_code == 200, r.text[:500]
        d = r.json()
        assert "nutella" in d["product_name"].lower(), d["product_name"]
        assert d["barcode"]["source"] == "openfoodfacts"
        assert d["barcode"]["code"] == NUTELLA
        assert int(d["total_ingredients"]) > 0
        assert "ai service" not in d["summary_ai"].lower(), d["summary_ai"]
        assert "temporarily unavailable" not in d["summary_ai"].lower()
        # persisted in history
        hist = api_client.get(f"{API}/history", headers=temp_headers, timeout=30).json()
        assert any(item["id"] == d["id"] for item in hist)


# ---------- profile avatar ----------
class TestAvatar:
    def _jpeg_data_url(self) -> str:
        img = Image.new("RGB", (24, 24), "blue")
        buf = io.BytesIO()
        img.save(buf, "JPEG")
        import base64

        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

    def test_avatar_persists(self, api_client, temp_headers):
        avatar = self._jpeg_data_url()
        put = api_client.put(
            f"{API}/profile",
            json={"goals": [], "allergies": [], "conditions": [], "medicines": [], "age": "30", "avatar": avatar},
            headers=temp_headers,
            timeout=30,
        )
        assert put.status_code == 200, put.text[:300]
        assert put.json()["avatar"] == avatar

        get = api_client.get(f"{API}/profile", headers=temp_headers, timeout=30)
        assert get.status_code == 200
        assert get.json()["avatar"] == avatar

    def test_avatar_invalid_data_url_400(self, api_client, temp_headers):
        r = api_client.put(f"{API}/profile", json={"avatar": "hello world"}, headers=temp_headers, timeout=30)
        assert r.status_code == 400, r.text[:300]

    def test_avatar_too_large_413(self, api_client, temp_headers):
        big = "data:image/jpeg;base64," + ("A" * 250_001)
        r = api_client.put(f"{API}/profile", json={"avatar": big}, headers=temp_headers, timeout=60)
        assert r.status_code == 413, f"expected 413, got {r.status_code}: {r.text[:200]}"

    def test_avatar_not_lost_on_unrelated_update(self, api_client, temp_headers):
        """Regression: saving other fields should not silently wipe the avatar."""
        avatar = self._jpeg_data_url()
        api_client.put(f"{API}/profile", json={"avatar": avatar}, headers=temp_headers, timeout=30)
        api_client.put(f"{API}/profile", json={"goals": ["low sugar"]}, headers=temp_headers, timeout=30)
        body = api_client.get(f"{API}/profile", headers=temp_headers, timeout=30).json()
        assert body["goals"] == ["low sugar"]
        assert body["avatar"] == avatar, "avatar wiped by a partial profile PUT"


# ---------- cleanup ----------
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data():
    yield
    import asyncio

    from motor.motor_asyncio import AsyncIOMotorClient

    env = dotenv_values("/app/backend/.env")
    if not env.get("MONGO_URL") or not env.get("DB_NAME"):
        return

    async def purge():
        cli = AsyncIOMotorClient(env["MONGO_URL"])
        db = cli[env["DB_NAME"]]
        users = [u async for u in db["users"].find({"email": {"$regex": "^test_.*@ingrelens.test$", "$options": "i"}})]
        ids = [u["id"] for u in users]
        if ids:
            await db["scans"].delete_many({"user_id": {"$in": ids}})
            await db["profiles"].delete_many({"user_id": {"$in": ids}})
            await db["users"].delete_many({"id": {"$in": ids}})
        cli.close()

    try:
        asyncio.new_event_loop().run_until_complete(purge())
    except Exception as exc:  # noqa: BLE001
        print(f"cleanup skipped: {exc}")
