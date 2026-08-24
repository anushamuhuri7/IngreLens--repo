"""Iteration 5: verify .gitignore no longer excludes the deploy-required env files."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from dotenv import dotenv_values

APP = Path("/app")


def _ignored(rel_path: str) -> bool:
    """True when git would exclude rel_path from the build context."""
    proc = subprocess.run(
        ["git", "check-ignore", "-q", rel_path],
        cwd=str(APP),
        capture_output=True,
    )
    # 0 => ignored, 1 => not ignored
    assert proc.returncode in (0, 1), proc.stderr.decode()
    return proc.returncode == 0


# ---------- gitignore build-context rules ----------
@pytest.mark.parametrize("rel", ["frontend/.env", "backend/.env"])
def test_required_env_files_not_ignored(rel):
    assert (APP / rel).exists(), f"/app/{rel} missing"
    assert not _ignored(rel), f"/app/{rel} is still excluded by .gitignore"


def test_generic_env_pattern_still_active():
    assert _ignored("some-other/.env"), "generic .env ignore rule was lost"
    assert _ignored("frontend/.env.local"), ".env.local ignore rule was lost"


def test_git_status_reports_env_files_as_untracked_not_ignored():
    out = subprocess.run(
        ["git", "status", "--porcelain", "frontend/.env", "backend/.env"],
        cwd=str(APP),
        capture_output=True,
        text=True,
    ).stdout
    assert "frontend/.env" in out
    assert "backend/.env" in out


# ---------- env file contents ----------
def test_frontend_env_keys():
    vals = dotenv_values(str(APP / "frontend/.env"))
    url = vals.get("REACT_APP_BACKEND_URL", "")
    assert url.startswith("https://"), f"bad REACT_APP_BACKEND_URL: {url!r}"


@pytest.mark.parametrize(
    "key", ["MONGO_URL", "DB_NAME", "SECRET_KEY", "EMERGENT_LLM_KEY", "CORS_ORIGINS"]
)
def test_backend_env_keys(key):
    vals = dotenv_values(str(APP / "backend/.env"))
    assert vals.get(key), f"{key} missing/empty in /app/backend/.env"
