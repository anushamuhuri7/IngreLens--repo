"""Deployment shim.

The Emergent FastAPI+React+Mongo template expects `/app/backend/server.py`
exposing `server:app`. Our actual FastAPI application lives at `app.main:app`
because the project was originally scaffolded as a Vite root project. This
shim re-exports the same FastAPI instance under the standard name so both
`uvicorn server:app` (cwd=/app/backend) and `uvicorn app.main:app` (cwd=/app)
resolve to the exact same application.

Keep this file thin — all application code stays in /app/app/.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the /app directory importable so `from app.main import app` works when
# uvicorn is launched from /app/backend.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.main import app  # noqa: E402,F401  — re-exported as `server.app`
