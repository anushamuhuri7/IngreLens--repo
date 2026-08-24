# IngreLens Product Requirements

## Original problem statement
Use the github repository and the video (for front-end), complete camera and OCR integration, ai comparison with profile, and finish the food/med label scanner and rating giver app IngreLens, completely.

## Architecture
- **Frontend**: React 18 + Vite + Tailwind, mobile-first shell matching the supplied recording.
- **Backend**: FastAPI + Motor (async MongoDB) on 0.0.0.0:8001; ingress proxies `/api/*`.
- **Persistence**: MongoDB (`MONGO_URL`, `DB_NAME=ingrelens`) with collections `users`, `profiles`, `scans`, `login_attempts`.
- **AI**: Claude Sonnet 5 via `emergentintegrations` (Emergent Universal Key) for personalised label analysis.
- **OCR**: Pytesseract server-side + browser camera capture with interactive crop.

## User personas
- Health-conscious shoppers checking food ingredients and nutrition concerns.
- People verifying medication directions, warnings, dosage and interactions.

## Core requirements
- Register/login with backend-stored bcrypt password hashes; per-user bearer sessions.
- Editable health profile (goals, allergies, conditions, medicines, age).
- Live camera capture, upload, interactive corner-drag crop, paste-text fallback, server OCR.
- AI-driven per-ingredient breakdown, safety score, verdict, personalised recommendations and (for MEDICINE) safety notice.
- Persistent scan history per user with search + delete.

## Implemented (2026-02)
- Full SQLite → MongoDB migration; single source of truth in `/app/backend/.env`.
- Claude Sonnet 5 integration (`app/ai_analyzer.py`) returning strict JSON reports.
- Interactive image crop overlay before analysis (`CropEditor` in `App.jsx`).
- Personalised "Recommendations" section rendered on the Results page.
- Seeded test account documented in `/app/memory/test_credentials.md`.
- Barcode scanner (ZXing) + backend enrichment via OpenFoodFacts (food) and OpenFDA (medicine) with multi-layout NDC + GTIN-13 handling.
- Real OCR: tesseract-ocr installed; preprocessing upgraded (EXIF transpose, upscaling, autocontrast, dual-PSM).
- Extracted text is surfaced back on the Results screen so users can verify what the AI actually read.
- Home news carousel with real links (Harvard, FDA, WHO, Mayo Clinic, AHA) — swipeable + prev/next controls.
- Profile picture upload (client-downscaled to 320×320 JPEG, stored as data URL, ≤250KB cap, server-side validation).
- Partial `PUT /api/profile` merges via `exclude_unset=True` so avatar/other fields are never wiped by unrelated updates.

## Prioritized backlog
- P1: Barcode lookup + branded product enrichment (OpenFoodFacts / DailyMed).
- P1: Streaming AI response so results feel instant.
- P2: Shareable PDF report of a scan.
- P2: Push/email reminders when a stored scan matches a newly-added allergy.

## Implemented (2026-06) — Vercel-only deployment migration
- Target platform is now VERCEL EXCLUSIVELY (user's explicit choice; no Emergent deploy).
- Backend runs as a Vercel Python serverless function: `/app/api/index.py` re-exports `app.main:app`; `vercel.json` rewrites `/api/(.*)` → `/api/index` with maxDuration 60.
- OCR moved to the BROWSER via tesseract.js v7 (`src/lib/ocr.js`); frontend sends only extracted text to `/api/scan` (no file upload). Server pytesseract kept behind an `OCR_AVAILABLE` import guard in `app/ocr_engine.py`.
- AI provider: user's own Google Gemini key (`gemini-3.6-flash`, direct REST via httpx in `app/ai_analyzer.py`). Priority: GEMINI_API_KEY > EMERGENT_LLM_KEY (Claude via lazy emergentintegrations import). Preview key lives in git-ignored `/app/.env`.
- Database: user's MongoDB Atlas cluster (creds in test_credentials.md); verified live from a clean venv simulating Vercel (register/profile/scan/history all pass on Atlas).
- Root `/app/requirements.txt` slimmed for the Vercel function (NO pytesseract/pillow/emergentintegrations/uvicorn; pymongo[srv] added). `/app/backend/requirements.txt` untouched (Emergent deployer manifest).
- Git state repaired: package-lock.json deleted+ignored, yarn.lock + both .env files committed; removed @supabase/supabase-js; deleted all dead SQLite/SQLAlchemy-era modules (app/routers, app/services, app/{auth,config,schemas,database,dependencies,models,analyzer,ai_explainer}.py, ingrelens.db, supabase_schema.sql, migrate_to_supabase.py, render.yaml).
- Bug fixes: post-login profile/history now fetched immediately (App.onAuthed); frontend reads backend URL from VITE_BACKEND_URL || REACT_APP_BACKEND_URL (envPrefix added) — for split hosting scenarios; Unsplash news image onError gradient fallback.
- Testing: iteration_11 — backend 26/26, all frontend flows pass incl. live browser OCR → Gemini scan.

## Vercel deployment runbook (for the user)
1. Save to GitHub, import repo in Vercel (framework auto-detected: Vite).
2. Set Environment Variables in Vercel → Settings: MONGO_URL (Atlas string), DB_NAME=ingrelens, SECRET_KEY (long random), GEMINI_API_KEY, GEMINI_MODEL=gemini-3.6-flash, CORS_ORIGINS=*.
3. Deploy. `/api/*` served by the Python function, frontend static from dist/.
