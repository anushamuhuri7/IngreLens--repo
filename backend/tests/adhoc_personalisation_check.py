"""Ad-hoc comparison: same food label with and without a conflicting profile."""
import json
import uuid

import requests

API = "https://cb5958a8-61bb-453d-9313-bce9a37c4b1e.preview.emergentagent.com/api"
LABEL = "Ingredients: Wheat flour, salt, sugar, peanut oil, MSG, sodium benzoate"


def reg(tag):
    email = f"TEST_cmp_{tag}_{uuid.uuid4().hex[:8]}@ingrelens.test"
    r = requests.post(API + "/auth/register", json={"name": "cmp", "email": email, "password": "Password123!"}, timeout=30)
    return {"Authorization": f"Bearer {r.json()['token']}"}


def scan(h):
    r = requests.post(API + "/scan", data={"text": LABEL, "mode": "FOOD"}, headers=h, timeout=120)
    return r.json()


plain = reg("plain")
base = scan(plain)
print("NO PROFILE -> score", base["safety_score"], "| verdict", base["overall_verdict"], "| match", base["profile_match"])
print("  summary:", base["summary_ai"][:200])

pers = reg("pers")
requests.put(API + "/profile", json={"goals": ["weight loss"], "allergies": ["peanut"], "conditions": ["hypertension"], "medicines": ["lisinopril"], "age": "40"}, headers=pers, timeout=30)
p = scan(pers)
print("WITH PROFILE -> score", p["safety_score"], "| verdict", p["overall_verdict"], "| match", p["profile_match"])
print("  summary:", p["summary_ai"][:300])
print("  flagged:", p["flagged_count"], "/", p["total_ingredients"])
print("  recs:", json.dumps(p["recommendations"], indent=1)[:400])
print("DELTA:", base["safety_score"] - p["safety_score"])
