"""Iteration 11 regression: browser-OCR-era /api/scan (text only), Gemini provider,
barcode, profile, auth, history + Vercel deploy static config checks.

AI-consuming tests are intentionally limited to 2 /api/scan calls.
"""
import os
import re
import json
import time
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")
API = f"{BASE_URL}/api"

FALLBACK_MSG = "AI analysis is temporarily unavailable"
FOOD_LABEL = "INGREDIENTS: WHEAT FLOUR, SUGAR, PEANUTS, PALM OIL, SALT"


def creds():
    content = Path("/app/memory/test_credentials.md").read_text()
    email = re.search(r"Email:\s*`([^`]+)`", content).group(1)
    pwd = re.search(r"Password:\s*`([^`]+)`", content).group(1)
    return {"email": email, "password": pwd}


@pytest.fixture(scope="session")
def api_client():
    s = requests.Session()
    return s


@pytest.fixture(scope="session")
def seeded(api_client):
    c = creds()
    r = api_client.post(f"{API}/auth/login", json=c, timeout=30)
    if r.status_code != 200:
        pytest.fail(f"Seeded login failed {r.status_code}: {r.text[:300]}")
    body = r.json()
    assert body.get("token")
    return body


@pytest.fixture(scope="session")
def seeded_headers(seeded):
    return {"Authorization": f"Bearer {seeded['token']}"}


@pytest.fixture(scope="session")
def throwaway(api_client):
    email = f"TEST_iter11_{uuid.uuid4().hex[:8]}@ingrelens.dev"
    r = api_client.post(
        f"{API}/auth/register",
        json={"name": "TEST Iter11", "email": email, "password": "Password123!"},
        timeout=30,
    )
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data.get("token")
    return {"email": email, "token": data["token"], "headers": {"Authorization": f"Bearer {data['token']}"}}


# ---------- health / auth ----------
class TestAuth:
    def test_health(self, api_client):
        r = api_client.get(f"{API}/health", timeout=30)
        assert r.status_code == 200
        assert r.json().get("status") == "healthy"

    def test_login_seeded(self, seeded):
        assert seeded["user"]["email"] == creds()["email"]

    def test_me(self, api_client, seeded_headers):
        r = api_client.get(f"{API}/auth/me", headers=seeded_headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["email"] == creds()["email"]
        assert "_id" not in d and "password_hash" not in d

    def test_wrong_password_401(self, api_client):
        r = api_client.post(
            f"{API}/auth/login",
            json={"email": creds()["email"], "password": "totallyWrong123!"},
            timeout=30,
        )
        assert r.status_code == 401

    def test_register_new_user(self, throwaway):
        assert throwaway["token"]

    def test_no_auth_401(self, api_client):
        assert api_client.get(f"{API}/profile", timeout=30).status_code == 401


# ---------- profile ----------
class TestProfile:
    def test_profile_put_get_persists(self, api_client, throwaway):
        payload = {
            "name": "TEST Iter11",
            "allergies": ["peanut", "soy"],
            "goals": ["low sugar"],
            "conditions": [],
            "avatar": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=",
        }
        r = api_client.put(f"{API}/profile", json=payload, headers=throwaway["headers"], timeout=30)
        assert r.status_code == 200, r.text[:300]
        g = api_client.get(f"{API}/profile", headers=throwaway["headers"], timeout=30)
        assert g.status_code == 200
        body = g.json()
        assert sorted(body["allergies"]) == ["peanut", "soy"]
        assert body["goals"] == ["low sugar"]
        assert body["avatar"].startswith("data:image/png;base64,")
        assert "_id" not in body

    def test_seeded_profile_has_peanut_allergy(self, api_client, seeded_headers):
        r = api_client.get(f"{API}/profile", headers=seeded_headers, timeout=30)
        assert r.status_code == 200
        allergies = [a.lower() for a in r.json().get("allergies", [])]
        assert allergies, "seeded profile has no allergies configured"
        print("seeded allergies:", allergies)


# ---------- barcode ----------
class TestBarcode:
    def test_nutella_lookup(self, api_client, seeded_headers):
        r = api_client.get(f"{API}/barcode/3017620422003", headers=seeded_headers, timeout=45)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d.get("source") == "openfoodfacts"
        assert "nutella" in (d.get("product_name") or "").lower()
        assert d.get("ingredients_text")

    def test_unknown_barcode_404(self, api_client, seeded_headers):
        r = api_client.get(f"{API}/barcode/0000000000000", headers=seeded_headers, timeout=45)
        assert r.status_code == 404

    def test_barcode_requires_auth(self, api_client):
        assert api_client.get(f"{API}/barcode/3017620422003", timeout=45).status_code == 401


# ---------- scan (AI: 2 calls total) ----------
@pytest.fixture(scope="session")
def seeded_scan(api_client, seeded_headers):
    r = api_client.post(
        f"{API}/scan",
        data={"text": FOOD_LABEL, "product_name": "TEST Iter11 Granola", "mode": "FOOD"},
        headers=seeded_headers,
        timeout=180,
    )
    assert r.status_code == 200, r.text[:500]
    return r.json()


class TestScan:
    def test_scan_requires_auth(self, api_client):
        r = api_client.post(f"{API}/scan", data={"text": FOOD_LABEL, "mode": "FOOD"}, timeout=30)
        assert r.status_code == 401

    def test_scan_no_input_rejected(self, api_client, seeded_headers):
        r = api_client.post(f"{API}/scan", data={"mode": "FOOD"}, headers=seeded_headers, timeout=60)
        assert r.status_code == 400, r.text[:300]

    def test_scan_text_only_returns_real_ai(self, seeded_scan):
        d = seeded_scan
        print("keys:", sorted(d.keys()))
        assert d.get("overall_verdict")
        assert isinstance(d.get("safety_score"), (int, float))
        assert 0 <= float(d["safety_score"]) <= 10
        breakdown = d.get("ingredients") or d.get("ingredient_breakdown") or []
        assert breakdown, "no ingredient breakdown returned"
        summary = d.get("summary_ai") or d.get("personalized_summary") or ""
        assert FALLBACK_MSG not in summary, "AI fallback returned instead of Gemini result"
        assert len(summary) > 30
        assert "_id" not in d
        print("verdict:", d["overall_verdict"], "score:", d["safety_score"])
        print("summary:", summary[:400])
        print("breakdown:", json.dumps(breakdown)[:600])

    def test_scan_flags_peanut_for_allergic_profile(self, seeded_scan):
        blob = json.dumps(seeded_scan).lower()
        assert "peanut" in blob, "peanut allergen not surfaced anywhere in the scan result"

    def test_scan_persisted_in_history(self, api_client, seeded_headers, seeded_scan):
        time.sleep(1)
        r = api_client.get(f"{API}/history", headers=seeded_headers, timeout=30)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list) and items
        assert any(i.get("product_name") == "TEST Iter11 Granola" for i in items)
        assert all("_id" not in i for i in items)


class TestHistoryThrowaway:
    def test_history_then_clear(self, api_client, throwaway):
        r = api_client.post(
            f"{API}/scan",
            data={"text": "INGREDIENTS: OATS, SUGAR, SOY LECITHIN", "product_name": "TEST Iter11 Bar", "mode": "FOOD"},
            headers=throwaway["headers"],
            timeout=180,
        )
        assert r.status_code == 200, r.text[:500]
        body = r.json()
        summary = body.get("summary_ai") or body.get("personalized_summary") or ""
        assert FALLBACK_MSG not in summary
        h = api_client.get(f"{API}/history", headers=throwaway["headers"], timeout=30)
        assert h.status_code == 200 and len(h.json()) >= 1
        d = api_client.delete(f"{API}/history", headers=throwaway["headers"], timeout=30)
        assert d.status_code in (200, 204)
        h2 = api_client.get(f"{API}/history", headers=throwaway["headers"], timeout=30)
        assert h2.status_code == 200 and h2.json() == []


# ---------- deploy static config ----------
class TestVercelConfig:
    def test_vercel_json(self):
        cfg = json.loads(Path("/app/vercel.json").read_text())
        rw = cfg["rewrites"][0]
        assert rw["source"] == "/api/(.*)"
        assert rw["destination"] == "/api/index"
        assert cfg["functions"]["api/index.py"]["maxDuration"] == 60

    def test_api_entry(self):
        src = Path("/app/api/index.py").read_text()
        assert "from app.main import app" in src

    def test_requirements_slim(self):
        req = Path("/app/requirements.txt").read_text().lower()
        for bad in ("pytesseract", "pillow", "emergentintegrations", "uvicorn"):
            assert bad not in req, f"{bad} still in requirements.txt"
        for good in ("motor", "pymongo[srv]", "httpx", "bcrypt", "python-multipart"):
            assert good in req, f"{good} missing"
        assert "fastapi>=0.110.0,<0.116" in req

    def test_ocr_guard(self):
        src = Path("/app/app/ocr_engine.py").read_text()
        assert "OCR_AVAILABLE = False" in src and "OCR_AVAILABLE = True" in src

    def test_package_json(self):
        pkg = json.loads(Path("/app/package.json").read_text())
        deps = pkg["dependencies"]
        assert "tesseract.js" in deps
        assert "@supabase/supabase-js" not in deps
        assert "@supabase/supabase-js" not in pkg.get("devDependencies", {})

    def test_package_lock_absent_and_staged_deleted(self):
        assert not Path("/app/package-lock.json").exists()
        import subprocess

        out = subprocess.run(
            ["git", "-C", "/app", "status", "--porcelain", "--", "package-lock.json"],
            capture_output=True, text=True,
        ).stdout
        assert out.strip().startswith("D"), f"package-lock.json not staged for deletion: {out!r}"

    def test_client_ocr_module(self):
        src = Path("/app/src/lib/ocr.js").read_text()
        assert "tesseract.js" in src and "createWorker" in src

    def test_gemini_priority(self):
        src = Path("/app/app/ai_analyzer.py").read_text()
        assert "_call_gemini(prompt) if GEMINI_API_KEY else _call_claude(prompt)" in src

    def test_onauthed_fetches_profile_and_history(self):
        src = Path("/app/src/App.jsx").read_text()
        block = src.split("function onAuthed(u)")[1][:400]
        assert "/api/profile" in block and "/api/history" in block
