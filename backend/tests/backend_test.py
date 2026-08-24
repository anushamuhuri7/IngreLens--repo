"""IngreLens backend regression suite — MongoDB + Claude Sonnet 5 migration.

Covers: health, auth (register/login/me/lockout), profile CRUD, scan (FOOD /
MEDICINE / personalisation / validation), history, and per-user isolation.
"""
from __future__ import annotations

import os
import re
import time
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values

# ---------- config ----------
frontend_env = dotenv_values("/app/frontend/.env") if Path("/app/frontend/.env").exists() else {}
base_url = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or frontend_env.get("REACT_APP_BACKEND_URL")
    or "https://cb5958a8-61bb-453d-9313-bce9a37c4b1e.preview.emergentagent.com"
)
BASE_URL = base_url.rstrip("/")
API = f"{BASE_URL}/api"
LLM_TIMEOUT = 120

FOOD_LABEL = "Ingredients: Wheat flour, salt, sugar, peanut oil, MSG, sodium benzoate"
MEDICINE_LABEL = "Paracetamol 500 mg, Active ingredient: acetaminophen, warnings: liver damage risk"

PROFILE_PAYLOAD = {
    "goals": ["low sodium"],
    "allergies": ["peanut"],
    "conditions": ["hypertension"],
    "medicines": ["lisinopril"],
    "age": "34",
}

REQUIRED_SCAN_KEYS = (
    "id", "created_at", "type", "safety_score", "overall_verdict", "ingredients",
    "profile_match", "summary_ai", "recommendations", "extracted_text",
    "total_ingredients", "flagged_count", "product_name",
)
INGREDIENT_KEYS = ("name", "risk_level", "hazard_score", "category", "description", "side_effects")


def _put_full_profile(api_client, headers):
    put = api_client.put(f"{API}/profile", json=PROFILE_PAYLOAD, headers=headers, timeout=30)
    assert put.status_code == 200, put.text[:300]
    returned = put.json()
    for key, value in PROFILE_PAYLOAD.items():
        assert returned[key] == value
    return returned


def _get_profile(api_client, headers):
    r = api_client.get(f"{API}/profile", headers=headers, timeout=30)
    assert r.status_code == 200
    return r.json()


def _assert_profile_matches(body):
    for key, value in PROFILE_PAYLOAD.items():
        assert body[key] == value, f"{key} not persisted"


def rand_email(tag: str = "user") -> str:
    return f"TEST_{tag}_{uuid.uuid4().hex[:10]}@ingrelens.test"


# ---------- fixtures ----------
@pytest.fixture(scope="session")
def api_client():
    session = requests.Session()
    return session


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def scan_user(api_client):
    """Dedicated account used for scan/history/profile mutation tests."""
    email = rand_email("scan")
    resp = api_client.post(
        f"{API}/auth/register",
        json={"name": "TEST Scan User", "email": email, "password": "Password123!"},
        timeout=30,
    )
    assert resp.status_code == 200, f"register failed {resp.status_code}: {resp.text[:300]}"
    data = resp.json()
    return {"email": email, "password": "Password123!", "token": data["token"], "id": data["user"]["id"]}


@pytest.fixture(scope="session")
def scan_headers(scan_user):
    return {"Authorization": f"Bearer {scan_user['token']}"}


# ---------- health ----------
class TestHealth:
    def test_health(self, api_client):
        r = api_client.get(f"{API}/health", timeout=30)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"
        assert body["service"] == "IngreLens Backend"
        assert body["db"]


# ---------- auth ----------
class TestAuth:
    def test_register_returns_token_and_user(self, api_client):
        email = rand_email("reg")
        r = api_client.post(
            f"{API}/auth/register",
            json={"name": "TEST Reg", "email": email, "password": "Password123!"},
            timeout=30,
        )
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert isinstance(data["token"], str) and len(data["token"]) > 10
        assert data["user"]["email"] == email.lower()  # server normalises email casing
        assert data["user"]["name"] == "TEST Reg"
        assert isinstance(data["user"]["id"], str)

        # token works immediately
        me = api_client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {data['token']}"}, timeout=30)
        assert me.status_code == 200
        assert me.json()["email"] == email.lower()

    def test_register_duplicate_email_conflicts(self, api_client):
        email = rand_email("dup")
        payload = {"name": "TEST Dup", "email": email, "password": "Password123!"}
        first = api_client.post(f"{API}/auth/register", json=payload, timeout=30)
        assert first.status_code == 200
        second = api_client.post(f"{API}/auth/register", json=payload, timeout=30)
        assert second.status_code == 409, f"expected 409, got {second.status_code}"
        assert "already exists" in second.json().get("detail", "").lower()

    def test_login_valid_credentials(self, api_client, seeded_credentials):
        r = api_client.post(f"{API}/auth/login", json=seeded_credentials, timeout=30)
        if r.status_code == 404 or (r.status_code == 401):
            # seed account may not exist yet -> create it, then retry
            api_client.post(
                f"{API}/auth/register",
                json={"name": "IngreLens QA", **seeded_credentials},
                timeout=30,
            )
            r = api_client.post(f"{API}/auth/login", json=seeded_credentials, timeout=30)
        assert r.status_code == 200, f"login failed {r.status_code}: {r.text[:300]}"
        data = r.json()
        assert data["user"]["email"] == seeded_credentials["email"]
        assert isinstance(data["token"], str)

    def test_login_invalid_password_401(self, api_client):
        email = rand_email("badpw")
        api_client.post(
            f"{API}/auth/register",
            json={"name": "TEST BadPw", "email": email, "password": "Password123!"},
            timeout=30,
        )
        r = api_client.post(f"{API}/auth/login", json={"email": email, "password": "WrongPassword1!"}, timeout=30)
        assert r.status_code == 401, r.text[:300]

    def test_login_unknown_email_401(self, api_client):
        r = api_client.post(
            f"{API}/auth/login",
            json={"email": rand_email("ghost"), "password": "Password123!"},
            timeout=30,
        )
        assert r.status_code == 401

    def test_brute_force_lockout_429(self, api_client):
        email = rand_email("lock")
        api_client.post(
            f"{API}/auth/register",
            json={"name": "TEST Lock", "email": email, "password": "Password123!"},
            timeout=30,
        )
        statuses = []
        for _ in range(5):
            resp = api_client.post(
                f"{API}/auth/login", json={"email": email, "password": "WrongPassword1!"}, timeout=30
            )
            statuses.append(resp.status_code)
        assert statuses == [401] * 5, f"expected five 401s, got {statuses}"

        sixth = api_client.post(
            f"{API}/auth/login", json={"email": email, "password": "WrongPassword1!"}, timeout=30
        )
        assert sixth.status_code == 429, f"expected 429 after 5 failures, got {sixth.status_code}"

        # correct password is also blocked while locked out
        locked = api_client.post(f"{API}/auth/login", json={"email": email, "password": "Password123!"}, timeout=30)
        assert locked.status_code == 429

    def test_me_without_token_401(self, api_client):
        r = api_client.get(f"{API}/auth/me", timeout=30)
        assert r.status_code == 401

    def test_me_with_tampered_token_401(self, api_client, scan_user):
        r = api_client.get(f"{API}/auth/me", headers={"Authorization": "Bearer abcdef123"}, timeout=30)
        assert r.status_code == 401

    def test_password_hash_is_bcrypt(self):
        """bcrypt hashes must be stored as $2b$ per the auth playbook."""
        import asyncio

        from motor.motor_asyncio import AsyncIOMotorClient

        backend_env = dotenv_values("/app/backend/.env")
        mongo_url = backend_env.get("MONGO_URL")
        db_name = backend_env.get("DB_NAME")
        if not mongo_url or not db_name:
            pytest.skip("MONGO_URL/DB_NAME unavailable")

        async def fetch():
            cli = AsyncIOMotorClient(mongo_url)
            doc = await cli[db_name]["users"].find_one({}, {"password": 1})
            cli.close()
            return doc

        doc = asyncio.get_event_loop().run_until_complete(fetch())
        assert doc, "no users found in database"
        assert doc["password"].startswith("$2b$"), f"unexpected hash prefix: {doc['password'][:7]}"


# ---------- profile ----------
class TestProfile:
    def test_profile_requires_auth(self, api_client):
        assert api_client.get(f"{API}/profile", timeout=30).status_code == 401
        assert api_client.put(f"{API}/profile", json={}, timeout=30).status_code == 401

    def test_default_profile_is_empty(self, api_client):
        email = rand_email("prof")
        reg = api_client.post(
            f"{API}/auth/register",
            json={"name": "TEST Prof", "email": email, "password": "Password123!"},
            timeout=30,
        )
        token = reg.json()["token"]
        r = api_client.get(f"{API}/profile", headers={"Authorization": f"Bearer {token}"}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data == {
            "goals": [],
            "allergies": [],
            "conditions": [],
            "medicines": [],
            "age": "",
            "avatar": "",
        }

    def test_profile_update_persists(self, api_client, scan_headers):
        _put_full_profile(api_client, scan_headers)
        body = _get_profile(api_client, scan_headers)
        _assert_profile_matches(body)

    def test_profile_get_after_put_excludes_internal_ids(self, api_client, scan_headers):
        body = _get_profile(api_client, scan_headers)
        assert "_id" not in body
        assert "user_id" not in body


# ---------- scan ----------
@pytest.fixture(scope="module")
def personalised_food_scan(api_client, scan_headers):
    """Run the personalised food scan once and share the result across tests."""
    profile = api_client.get(f"{API}/profile", headers=scan_headers, timeout=30).json()
    assert profile["allergies"] == ["peanut"], "profile precondition missing"
    r = api_client.post(
        f"{API}/scan",
        data={"text": FOOD_LABEL, "mode": "FOOD", "product_name": "TEST Snack"},
        headers=scan_headers,
        timeout=LLM_TIMEOUT,
    )
    assert r.status_code == 200, r.text[:400]
    return r.json()


class TestScan:
    def test_scan_requires_auth(self, api_client):
        r = api_client.post(f"{API}/scan", data={"text": FOOD_LABEL, "mode": "FOOD"}, timeout=30)
        assert r.status_code == 401

    def test_scan_without_file_or_text_400(self, api_client, scan_headers):
        r = api_client.post(f"{API}/scan", data={"mode": "FOOD"}, headers=scan_headers, timeout=60)
        assert r.status_code == 400, r.text[:300]

    def test_food_scan_has_all_required_keys(self, personalised_food_scan):
        for key in REQUIRED_SCAN_KEYS:
            assert key in personalised_food_scan, f"missing key {key}"
        assert "_id" not in personalised_food_scan

    def test_food_scan_type_and_extracted_text(self, personalised_food_scan):
        assert personalised_food_scan["type"] == "FOOD"
        assert personalised_food_scan["extracted_text"].strip().startswith("Ingredients:")

    def test_food_scan_score_and_ingredients_shape(self, personalised_food_scan):
        d = personalised_food_scan
        assert 0 <= float(d["safety_score"]) <= 10
        assert isinstance(d["ingredients"], list) and len(d["ingredients"]) >= 3
        first = d["ingredients"][0]
        for key in INGREDIENT_KEYS:
            assert key in first
        assert first["risk_level"] in {"Safe", "Caution", "Hazardous"}

    def test_food_scan_uses_real_llm_not_fallback(self, personalised_food_scan):
        d = personalised_food_scan
        assert d["summary_ai"].strip(), "summary_ai empty -> LLM fallback"
        assert len(d["recommendations"]) >= 2
        assert d["medicine_notice"] == ""
        assert "temporarily unavailable" not in d["summary_ai"]
        assert "not configured" not in d["summary_ai"]

    def test_food_scan_personalisation_reflects_profile(self, personalised_food_scan):
        d = personalised_food_scan
        assert d["profile_match"], "profile_match empty despite peanut allergy in profile"
        matched = " ".join(d["profile_match"]).lower()
        assert any(t in matched for t in ("peanut", "hypertension", "sodium", "salt", "lisinopril")), d["profile_match"]
        assert float(d["safety_score"]) <= 5.0
        assert d["overall_verdict"] in {"Avoid", "Personal caution", "Moderate Risk"}

    def test_medicine_scan_returns_notice(self, api_client, scan_headers):
        r = api_client.post(
            f"{API}/scan",
            data={"text": MEDICINE_LABEL, "mode": "MEDICINE", "product_name": "TEST Paracetamol"},
            headers=scan_headers,
            timeout=LLM_TIMEOUT,
        )
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d["type"] == "MEDICINE"
        assert d["medicine_notice"].strip(), "medicine_notice empty for MEDICINE mode"
        assert "temporarily unavailable" not in d["summary_ai"]
        assert d["ingredients"], "no ingredients parsed for medicine label"

    def test_invalid_mode_defaults_to_food(self, api_client, scan_headers):
        r = api_client.post(
            f"{API}/scan",
            data={"text": FOOD_LABEL, "mode": "SOMETHING"},
            headers=scan_headers,
            timeout=LLM_TIMEOUT,
        )
        assert r.status_code == 200, r.text[:300]
        assert r.json()["type"] == "FOOD"


# ---------- history & isolation ----------
class TestHistory:
    def test_history_requires_auth(self, api_client):
        assert api_client.get(f"{API}/history", timeout=30).status_code == 401
        assert api_client.delete(f"{API}/history", timeout=30).status_code == 401

    def test_history_contains_scans_newest_first(self, api_client, scan_headers, scan_user):
        r = api_client.get(f"{API}/history", headers=scan_headers, timeout=30)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list) and len(items) >= 2, f"expected >=2 scans, got {len(items)}"
        assert all("_id" not in i for i in items)
        assert all(i["user_id"] == scan_user["id"] for i in items)
        created = [i["created_at"] for i in items]
        assert created == sorted(created, reverse=True), "history not sorted newest first"

    def test_user_isolation(self, api_client, scan_headers):
        other_email = rand_email("iso")
        reg = api_client.post(
            f"{API}/auth/register",
            json={"name": "TEST Iso", "email": other_email, "password": "Password123!"},
            timeout=30,
        )
        other_headers = {"Authorization": f"Bearer {reg.json()['token']}"}

        assert api_client.get(f"{API}/history", headers=other_headers, timeout=30).json() == []
        other_profile = api_client.get(f"{API}/profile", headers=other_headers, timeout=30).json()
        assert other_profile["allergies"] == [], "profile leaked across users"

        # the primary user still sees their own scans
        mine = api_client.get(f"{API}/history", headers=scan_headers, timeout=30).json()
        assert len(mine) >= 2

    def test_clear_history(self, api_client, scan_headers):
        before = api_client.get(f"{API}/history", headers=scan_headers, timeout=30).json()
        assert before, "no scans to clear"
        d = api_client.delete(f"{API}/history", headers=scan_headers, timeout=30)
        assert d.status_code == 200
        body = d.json()
        assert body["cleared"] == True  # noqa: E712 — explicit boolean check per code review
        assert body["removed"] == len(before), f"removed={body['removed']} vs {len(before)}"

        after = api_client.get(f"{API}/history", headers=scan_headers, timeout=30).json()
        assert after == []


# ---------- cleanup ----------
@pytest.fixture(scope="session", autouse=True)
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
        await db["login_attempts"].delete_many({"key": {"$regex": "^login:test_", "$options": "i"}})
        cli.close()

    try:
        asyncio.new_event_loop().run_until_complete(purge())
    except Exception as exc:  # noqa: BLE001
        print(f"cleanup skipped: {exc}")
    _ = time.time
