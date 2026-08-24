"""Iteration 8 — deploy-readiness verification smoke suite.

Verifies the four deployment-critical state items plus a live endpoint smoke
(health, seeded QA login, profile avatar persistence, barcode lookup, scan).
No application code is modified by this suite.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values
from packaging.requirements import Requirement

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL is missing from env and /app/frontend/.env")
BASE_URL = base_url.rstrip("/")

REPO = Path("/app")
BARCODE_NUTELLA = "3017620422003"


# ---------------------------------------------------------------- credentials
@pytest.fixture(scope="session")
def creds():
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
def token(creds):
    r = requests.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=45)
    if r.status_code != 200:
        pytest.fail(f"Seeded QA login failed: {r.status_code} {r.text[:400]}")
    body = r.json()
    tok = body.get("token") or body.get("access_token")
    assert isinstance(tok, str) and tok, f"No token in login response: {body}"
    return tok


@pytest.fixture(scope="session")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------- state item 1 & 2: .env tracked
class TestEnvFilesNotGitIgnored:
    @pytest.mark.parametrize("rel", ["frontend/.env", "backend/.env"])
    def test_env_file_exists(self, rel):
        p = REPO / rel
        assert p.is_file(), f"{rel} is missing"
        assert p.stat().st_size > 0, f"{rel} is empty"

    @pytest.mark.parametrize("rel", ["frontend/.env", "backend/.env"])
    def test_env_file_not_git_ignored(self, rel):
        proc = subprocess.run(
            ["git", "check-ignore", "-q", rel], cwd=REPO, capture_output=True
        )
        # rc 0 => ignored (bad), rc 1 => not ignored (good)
        assert proc.returncode == 1, f"{rel} IS git-ignored (rc={proc.returncode})"

    @pytest.mark.parametrize("neg", ["!frontend/.env", "!backend/.env"])
    def test_gitignore_negations_present(self, neg):
        text = (REPO / ".gitignore").read_text(encoding="utf-8")
        assert neg in text.splitlines(), f"{neg} negation missing from .gitignore"

    def test_protected_keys_present(self):
        be = dotenv_values("/app/backend/.env")
        fe = dotenv_values("/app/frontend/.env")
        assert be.get("MONGO_URL"), "MONGO_URL missing in backend/.env"
        assert be.get("DB_NAME"), "DB_NAME missing in backend/.env"
        assert fe.get("REACT_APP_BACKEND_URL"), "REACT_APP_BACKEND_URL missing"


# ------------------------------------------- state item 3: requirements pins
class TestRequirementsManifest:
    @pytest.fixture(scope="class")
    def reqs(self):
        lines = (REPO / "backend/requirements.txt").read_text(encoding="utf-8").splitlines()
        out = {}
        for line in lines:
            line = line.split("#")[0].strip()
            if not line or line.startswith("-"):
                continue
            req = Requirement(line)
            out[req.name.lower()] = req
        return out

    def test_fastapi_upper_bound_below_0_116(self, reqs):
        assert "fastapi" in reqs, "fastapi missing from backend/requirements.txt"
        spec = reqs["fastapi"].specifier
        assert spec.contains("0.115.14"), f"fastapi spec {spec} rejects 0.115.14"
        assert not spec.contains("0.116.0"), f"fastapi spec {spec} allows 0.116.0"
        assert not spec.contains("0.141.0"), f"fastapi spec {spec} allows 0.141.0"

    def test_annotated_doc_present(self, reqs):
        assert "annotated-doc" in reqs, "annotated-doc missing (prod ModuleNotFoundError)"

    def test_click_present(self, reqs):
        assert "click" in reqs, "click missing from backend/requirements.txt"

    def test_root_and_backend_manifests_identical(self):
        root = REPO / "requirements.txt"
        if not root.is_file():
            pytest.skip("no root requirements.txt")
        assert root.read_bytes() == (REPO / "backend/requirements.txt").read_bytes(), (
            "root and backend requirements.txt have drifted"
        )


# ------------------------------------------------- state item 4: server shim
class TestServerShim:
    def test_server_app_is_same_instance_as_app_main(self):
        code = (
            "import sys; sys.path.insert(0,'/app/backend'); sys.path.insert(0,'/app');\n"
            "import server, app.main;\n"
            "assert server.app is app.main.app, 'different FastAPI instances';\n"
            "print(server.app.title)"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code], cwd="/app/backend", capture_output=True, text=True
        )
        assert proc.returncode == 0, f"shim import failed:\n{proc.stderr[-2000:]}"
        assert proc.stdout.strip(), "no app title printed"

    def test_server_app_exposes_api_routes(self):
        code = (
            "import sys; sys.path.insert(0,'/app/backend');\n"
            "import server;\n"
            "paths=[r.path for r in server.app.routes];\n"
            "assert any(p.startswith('/api') for p in paths), paths;\n"
            "print(len(paths))"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code], cwd="/app/backend", capture_output=True, text=True
        )
        assert proc.returncode == 0, proc.stderr[-2000:]
        assert int(proc.stdout.strip()) > 0


# --------------------------------------------------------------- live smoke
class TestLiveSmoke:
    def test_health(self):
        r = requests.get(f"{BASE_URL}/api/health", timeout=45)
        assert r.status_code == 200, r.text[:400]
        body = r.json()
        assert body.get("status") == "healthy", body

    def test_login_returns_token(self, token):
        assert len(token) > 20

    def test_profile_returns_saved_avatar(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/profile", headers=auth_headers, timeout=45)
        assert r.status_code == 200, r.text[:400]
        body = r.json()
        assert "_id" not in body, "MongoDB _id leaked in /api/profile"
        assert body.get("avatar"), f"avatar not persisted: {body}"

    def test_barcode_lookup_nutella(self, auth_headers):
        r = requests.get(
            f"{BASE_URL}/api/barcode/{BARCODE_NUTELLA}?mode=FOOD",
            headers=auth_headers,
            timeout=60,
        )
        assert r.status_code == 200, r.text[:400]
        body = r.json()
        assert "_id" not in body
        blob = str(body).lower()
        assert "nutella" in blob, f"Nutella not found in barcode response: {body}"

    def test_scan_barcode_only_returns_claude_analysis(self, auth_headers):
        r = requests.post(
            f"{BASE_URL}/api/scan",
            headers=auth_headers,
            data={"barcode": BARCODE_NUTELLA, "mode": "FOOD"},
            timeout=180,
        )
        assert r.status_code == 200, r.text[:600]
        body = r.json()
        assert "_id" not in body
        ingredients = body.get("ingredients") or body.get("analysis", {}).get("ingredients")
        assert ingredients, f"no ingredients in scan analysis: {str(body)[:600]}"
        assert len(ingredients) > 0
        # must be a real Claude analysis, not the offline fallback
        blob = str(body).lower()
        assert "fallback" not in blob, f"scan returned fallback analysis: {str(body)[:600]}"
        assert body.get("barcode", {}).get("code") == BARCODE_NUTELLA, body.get("barcode")
