"""Iteration 4: post deployment-config-fix regression checks (frontend/.env added)."""
from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values

FRONTEND_ENV = Path("/app/frontend/.env")
frontend_env = dotenv_values(str(FRONTEND_ENV)) if FRONTEND_ENV.exists() else {}
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing from env and /app/frontend/.env")
API = base_url.rstrip("/") + "/api"

CREDS_FILE = Path("/app/memory/test_credentials.md")
NUTELLA = "3017620422003"


# ---------- frontend env config ----------
def test_frontend_env_file_exists_with_backend_url():
    assert FRONTEND_ENV.exists(), "/app/frontend/.env is missing"
    val = frontend_env.get("REACT_APP_BACKEND_URL", "")
    assert val.startswith("https://"), f"unexpected REACT_APP_BACKEND_URL: {val!r}"
    assert "preview.emergentagent.com" in val


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    yield s
    s.close()


@pytest.fixture(scope="module")
def seeded_creds():
    if not CREDS_FILE.exists():
        pytest.skip("missing /app/memory/test_credentials.md")
    content = CREDS_FILE.read_text()
    email = re.search(r"(?im)^\s*[-*]?\s*email\s*:\s*`?([^`\s]+)", content)
    pwd = re.search(r"(?im)^\s*[-*]?\s*password\s*:\s*`?([^`\s]+)", content)
    if not email or not pwd:
        pytest.skip("no credentials parsed from test_credentials.md")
    return {"email": email.group(1), "password": pwd.group(1)}


# ---------- health ----------
def test_health(client):
    r = client.get(f"{API}/health", timeout=30)
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


# ---------- fresh register + login ----------
def test_register_then_login_fresh_user(client):
    email = f"TEST_{uuid.uuid4().hex[:10]}@ingrelens.test"
    r = client.post(
        f"{API}/auth/register",
        json={"name": "TEST Deploy", "email": email, "password": "Password123!"},
        timeout=45,
    )
    assert r.status_code in (200, 201), r.text[:300]
    assert r.json()["token"]
    r2 = client.post(
        f"{API}/auth/login", json={"email": email, "password": "Password123!"}, timeout=45
    )
    assert r2.status_code == 200, r2.text[:300]
    token = r2.json()["token"]
    me = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=30)
    assert me.status_code == 200
    assert me.json()["email"] == email.lower()


# ---------- seeded QA account ----------
@pytest.fixture(scope="module")
def seed_token(client, seeded_creds):
    r = client.post(f"{API}/auth/login", json=seeded_creds, timeout=45)
    if r.status_code != 200:
        pytest.fail(f"seeded QA login failed {r.status_code}: {r.text[:300]}")
    return r.json()["token"]


def test_seeded_profile_has_avatar(client, seed_token):
    r = client.get(f"{API}/profile", headers={"Authorization": f"Bearer {seed_token}"}, timeout=30)
    assert r.status_code == 200, r.text[:300]
    p = r.json()
    assert "avatar" in p, p.keys()
    assert "_id" not in p
    assert p["avatar"].startswith("data:image/"), f"avatar not preserved: {p['avatar'][:40]!r}"


def test_partial_put_keeps_avatar(client, seed_token):
    h = {"Authorization": f"Bearer {seed_token}"}
    before = client.get(f"{API}/profile", headers=h, timeout=30).json()
    r = client.put(f"{API}/profile", json={"goals": ["low sugar"]}, headers=h, timeout=30)
    assert r.status_code == 200, r.text[:300]
    after = client.get(f"{API}/profile", headers=h, timeout=30).json()
    assert after["avatar"] == before["avatar"], "partial PUT wiped avatar"
    assert after["goals"] == ["low sugar"]


# ---------- barcode + scan ----------
def test_barcode_food_nutella(client, seed_token):
    r = client.get(
        f"{API}/barcode/{NUTELLA}?mode=FOOD",
        headers={"Authorization": f"Bearer {seed_token}"},
        timeout=60,
    )
    assert r.status_code == 200, r.text[:300]
    d = r.json()
    assert "nutella" in d["product_name"].lower()
    assert d["source"] == "openfoodfacts"
    assert d["packed_text"].strip()


def test_scan_by_barcode_returns_real_analysis(client, seed_token):
    r = client.post(
        f"{API}/scan",
        data={"barcode": NUTELLA},
        headers={"Authorization": f"Bearer {seed_token}"},
        timeout=180,
    )
    assert r.status_code == 200, r.text[:400]
    d = r.json()
    assert "nutella" in (d.get("product_name") or "").lower()
    assert d["total_ingredients"] > 0
    blob = str(d).lower()
    assert "ai service" not in blob and "unavailable" not in blob, blob[:300]
