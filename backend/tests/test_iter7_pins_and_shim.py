"""Iteration 7 — verify the fastapi upper-bound pin + /app/backend/server.py shim.

Covers:
  * both manifests pin fastapi < 0.116 and bound uvicorn/starlette/pydantic
  * annotated-doc + click declared explicitly
  * production install path simulated via `pip install --dry-run --report -`
    -> exit 0, fastapi resolved < 0.116, annotated-doc in the plan
  * `server:app` importable with cwd=/app/backend (deployer entry point)
  * `app.main:app` importable with cwd=/app (preview entry point)
  * both entry points expose the same app title
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.version import Version

BACKEND_REQ = Path("/app/backend/requirements.txt")
ROOT_REQ = Path("/app/requirements.txt")
SHIM = Path("/app/backend/server.py")
APP_TITLE = "IngreLens API"

REQUIRED_PACKAGES = [
    "fastapi", "uvicorn", "click", "starlette", "pydantic", "annotated-doc",
    "motor", "pymongo", "python-multipart", "pillow", "pytesseract",
    "python-dotenv", "httpx", "bcrypt", "emergentintegrations",
]

MANIFESTS = [BACKEND_REQ, ROOT_REQ]


def _parse(path: Path):
    out = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        req = Requirement(line)
        out[req.name.lower().replace("_", "-")] = req
    return out


def _upper_bound(req: Requirement):
    for spec in req.specifier:
        if spec.operator in ("<", "<="):
            return Version(spec.version)
    return None


# --- manifest correctness ---------------------------------------------------
class TestManifestPins:
    @pytest.mark.parametrize("path", MANIFESTS, ids=lambda p: str(p))
    @pytest.mark.parametrize("pkg", REQUIRED_PACKAGES)
    def test_package_declared(self, path, pkg):
        parsed = _parse(path)
        assert pkg in parsed, f"{pkg} missing from {path}: {sorted(parsed)}"

    @pytest.mark.parametrize("path", MANIFESTS, ids=lambda p: str(p))
    def test_fastapi_upper_bound_excludes_annotated_doc_era(self, path):
        req = _parse(path)["fastapi"]
        ub = _upper_bound(req)
        assert ub is not None, f"fastapi has no upper bound in {path}: {req}"
        assert ub <= Version("0.116"), f"fastapi upper bound too loose in {path}: {req}"
        assert req.specifier.contains("0.110.1"), f"0.110.1 not allowed by {req}"
        assert not req.specifier.contains("0.141.0"), f"{req} still allows fastapi 0.141"

    @pytest.mark.parametrize("path", MANIFESTS, ids=lambda p: str(p))
    def test_uvicorn_bounded_with_standard_extra(self, path):
        req = _parse(path)["uvicorn"]
        assert "standard" in req.extras, f"expected uvicorn[standard] in {path}: {req}"
        ub = _upper_bound(req)
        assert ub is not None and ub <= Version("0.35"), f"uvicorn upper bound missing/loose: {req}"

    @pytest.mark.parametrize("path", MANIFESTS, ids=lambda p: str(p))
    def test_starlette_bounded(self, path):
        assert _upper_bound(_parse(path)["starlette"]) is not None

    @pytest.mark.parametrize("path", MANIFESTS, ids=lambda p: str(p))
    def test_pydantic_bounded_below_v3(self, path):
        req = _parse(path)["pydantic"]
        ub = _upper_bound(req)
        assert ub is not None and ub <= Version("3.0"), f"pydantic upper bound missing/loose: {req}"
        assert not req.specifier.contains("3.0.0")

    @pytest.mark.parametrize("path", MANIFESTS, ids=lambda p: str(p))
    def test_annotated_doc_and_click_minimums(self, path):
        parsed = _parse(path)
        assert parsed["annotated-doc"].specifier.contains("0.0.5")
        assert not parsed["annotated-doc"].specifier.contains("0.0.4")
        assert parsed["click"].specifier.contains("8.1.0")
        assert not parsed["click"].specifier.contains("8.0.0")

    def test_manifests_identical(self):
        assert BACKEND_REQ.read_text().split() == ROOT_REQ.read_text().split()


# --- production install path ------------------------------------------------
class TestPipDryRun:
    @pytest.fixture(scope="class")
    def report(self):
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--dry-run", "--quiet",
             "--report", "-", "-r", str(BACKEND_REQ)],
            capture_output=True, text=True, timeout=900,
        )
        if proc.returncode != 0:
            pytest.fail(f"pip dry-run failed rc={proc.returncode}:\n"
                        f"{(proc.stdout or '')[-1500:]}\n{(proc.stderr or '')[-3000:]}")
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            pytest.fail(f"could not parse pip report JSON: {proc.stdout[:1000]}")
        versions = {}
        for item in data.get("install", []):
            meta = item.get("metadata", {})
            versions[meta.get("name", "").lower().replace("_", "-")] = meta.get("version")
        return {"rc": proc.returncode, "versions": versions, "raw": proc.stdout}

    def test_dry_run_exit_zero(self, report):
        assert report["rc"] == 0

    def test_fastapi_resolved_below_0116(self, report):
        v = report["versions"].get("fastapi")
        if v is None:
            # already satisfied in the env -> assert installed version instead
            import fastapi
            v = fastapi.__version__
        assert Version(v) < Version("0.116"), f"resolver picked fastapi {v}"

    def test_annotated_doc_in_plan_or_installed(self, report):
        if "annotated-doc" not in report["versions"]:
            proc = subprocess.run([sys.executable, "-m", "pip", "show", "annotated-doc"],
                                  capture_output=True, text=True)
            assert proc.returncode == 0, ("annotated-doc neither in install plan nor installed:\n"
                                          f"{sorted(report['versions'])}")

    def test_no_resolver_conflict(self, report):
        low = report["raw"].lower()
        for bad in ("resolutionimpossible", "conflict is caused by"):
            assert bad not in low


# --- entry points -----------------------------------------------------------
def _import_title(module: str, cwd: str):
    proc = subprocess.run(
        [sys.executable, "-c", f"from {module} import app; print(app.title)"],
        cwd=cwd, capture_output=True, text=True, timeout=180,
    )
    return proc


class TestEntryPoints:
    def test_shim_file_thin_and_reexports(self):
        assert SHIM.is_file(), "/app/backend/server.py missing — deployer `server:app` will fail"
        text = SHIM.read_text()
        assert "from app.main import app" in text
        assert len([l for l in text.splitlines() if l.strip()]) < 40, "shim should stay thin"

    def test_server_app_importable_from_backend_cwd(self):
        proc = _import_title("server", "/app/backend")
        assert proc.returncode == 0, f"`from server import app` failed:\n{proc.stderr[-3000:]}"
        assert proc.stdout.strip() == APP_TITLE, proc.stdout

    def test_app_main_importable_from_root_cwd(self):
        proc = _import_title("app.main", "/app")
        assert proc.returncode == 0, f"`from app.main import app` failed:\n{proc.stderr[-3000:]}"
        assert proc.stdout.strip() == APP_TITLE, proc.stdout

    def test_both_entry_points_same_app_object(self):
        code = (
            "import sys; sys.path.insert(0, '/app');"
            "import server, app.main;"
            "print(server.app is app.main.app)"
        )
        proc = subprocess.run([sys.executable, "-c", code], cwd="/app/backend",
                              capture_output=True, text=True, timeout=180)
        assert proc.returncode == 0, proc.stderr[-3000:]
        assert proc.stdout.strip() == "True", f"server:app is a different instance: {proc.stdout}"

    def test_shim_exposes_api_routes(self):
        code = ("from server import app;"
                "paths=[r.path for r in app.routes];"
                "print(any(p.startswith('/api') for p in paths), len(paths))")
        proc = subprocess.run([sys.executable, "-c", code], cwd="/app/backend",
                              capture_output=True, text=True, timeout=180)
        assert proc.returncode == 0, proc.stderr[-3000:]
        assert proc.stdout.strip().startswith("True"), proc.stdout


# --- runtime health ---------------------------------------------------------
def test_installed_fastapi_matches_pin():
    import fastapi
    req = _parse(BACKEND_REQ)["fastapi"]
    assert req.specifier.contains(fastapi.__version__), \
        f"installed fastapi {fastapi.__version__} violates manifest pin {req}"
