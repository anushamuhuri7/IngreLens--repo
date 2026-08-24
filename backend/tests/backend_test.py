import os
import uuid
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")


def test_auth_profile_scan_history_isolation():
    suffix = uuid.uuid4().hex[:8]
    s1 = requests.Session()
    payload = {"name": "TEST User", "email": f"test_{suffix}@example.com", "password": "password123"}
    r = s1.post(f"{BASE_URL}/api/auth/register", json=payload)
    assert r.status_code == 200 and r.json()["token"]
    s1.headers["Authorization"] = f"Bearer {r.json()['token']}"
    assert s1.get(f"{BASE_URL}/api/auth/me").json()["email"] == payload["email"]
    assert s1.put(f"{BASE_URL}/api/profile", json={"goals": ["Low sodium"], "allergies": ["peanut"], "conditions": [], "medicines": [], "age": "30"}).status_code == 200
    scan = s1.post(f"{BASE_URL}/api/scan", data={"text": "Ingredients: oats, peanut, sugar", "product_name": "TEST Oats", "mode": "FOOD"})
    assert scan.status_code == 200
    assert "peanut" in scan.json()["profile_match"]
    assert len(s1.get(f"{BASE_URL}/api/history").json()) == 1
    assert s1.post(f"{BASE_URL}/api/auth/login", json={"email": payload["email"], "password": "wrongpass"}).status_code == 401
    r2 = requests.post(f"{BASE_URL}/api/auth/register", json={"name": "Other", "email": f"other_{suffix}@example.com", "password": "password123"})
    s2 = requests.Session(); s2.headers["Authorization"] = f"Bearer {r2.json()['token']}"
    assert s2.get(f"{BASE_URL}/api/history").json() == []


def test_medicine_scan_disclaimer_and_validation():
    suffix = uuid.uuid4().hex[:8]
    r = requests.post(f"{BASE_URL}/api/auth/register", json={"name": "Med", "email": f"med_{suffix}@example.com", "password": "password123"})
    s = requests.Session(); s.headers["Authorization"] = f"Bearer {r.json()['token']}"
    result = s.post(f"{BASE_URL}/api/scan", data={"text": "Active ingredient, dosage, directions", "product_name": "TEST Med", "mode": "MEDICINE"})
    assert result.status_code == 200 and result.json()["medicine_notice"]
    assert s.post(f"{BASE_URL}/api/scan", data={"product_name": "Empty", "mode": "FOOD"}).status_code == 400