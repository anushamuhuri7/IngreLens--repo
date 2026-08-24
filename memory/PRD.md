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
