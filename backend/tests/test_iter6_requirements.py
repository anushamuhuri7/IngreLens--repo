"""Iteration 6 — deployment dependency-manifest verification.

Covers:
  * /app/backend/requirements.txt exists with the full production dependency set
  * /app/requirements.txt still declares click + starlette for the preview env
  * pip resolver dry-run on /app/backend/requirements.txt installs `click`
  * preview backend is still healthy (module imports resolved at runtime)
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_REQ = Path("/app/backend/requirements.txt")
ROOT_REQ = Path("/app/requirements.txt")

REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "click",
    "starlette",
    "pydantic",
    "motor",
    "pymongo",
    "python-multipart",
    "pillow",
    "pytesseract",
    "python-dotenv",
    "httpx",
    "bcrypt",
    "emergentintegrations",
]


def _parse(path: Path):
    """Return {normalised_name: raw_line} for a requirements file."""
    out = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        name = re.split(r"[\[<>=!~;]", line, maxsplit=1)[0].strip().lower().replace("_", "-")
        out[name] = line
    return out


# --- manifest existence / contents -----------------------------------------
class TestRequirementManifests:
    def test_backend_requirements_exists(self):
        assert BACKEND_REQ.is_file(), f"{BACKEND_REQ} missing — production image will not install deps"
        assert BACKEND_REQ.stat().st_size > 0

    @pytest.mark.parametrize("pkg", REQUIRED_PACKAGES)
    def test_backend_requirements_contains_package(self, pkg):
        parsed = _parse(BACKEND_REQ)
        assert pkg in parsed, f"{pkg} missing from {BACKEND_REQ}: {sorted(parsed)}"

    def test_uvicorn_has_standard_extra(self):
        line = _parse(BACKEND_REQ)["uvicorn"]
        assert "[standard]" in line, f"expected uvicorn[standard], got {line!r}"

    def test_root_requirements_has_click_and_starlette(self):
        parsed = _parse(ROOT_REQ)
        assert "click" in parsed, "click missing from /app/requirements.txt"
        assert "starlette" in parsed, "starlette missing from /app/requirements.txt"

    def test_root_and_backend_manifests_consistent(self):
        root, backend = _parse(ROOT_REQ), _parse(BACKEND_REQ)
        missing_in_backend = set(root) - set(backend)
        assert not missing_in_backend, f"root-only deps absent from backend manifest: {missing_in_backend}"

    def test_no_duplicate_or_malformed_lines(self):
        raw_names = []
        for line in BACKEND_REQ.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            assert re.match(r"^[A-Za-z0-9._\-]+(\[[a-z,]+\])?\s*([<>=!~].+)?$", line), f"malformed: {line!r}"
            raw_names.append(re.split(r"[\[<>=!~]", line)[0].lower())
        assert len(raw_names) == len(set(raw_names)), f"duplicate entries: {raw_names}"


# --- resolver simulation of the production install path ---------------------
class TestPipResolution:
    def test_dry_run_resolves_click(self):
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--dry-run",
             "--report", "-", "-r", str(BACKEND_REQ)],
            capture_output=True, text=True, timeout=600,
        )
        combined = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0:
            pytest.fail(f"pip dry-run failed (rc={proc.returncode}):\n{combined[-3000:]}")
        assert "click" in combined.lower(), "click not present in pip resolution report"
        for bad in ("ResolutionImpossible", "conflict is caused by", "ERROR:"):
            assert bad not in combined, f"resolver problem ({bad}):\n{combined[-2000:]}"

    def test_click_and_uvicorn_importable_in_env(self):
        import click  # noqa: F401
        import uvicorn  # noqa: F401

        assert click.__version__.split(".")[0].isdigit()
        assert int(click.__version__.split(".")[0]) >= 8
