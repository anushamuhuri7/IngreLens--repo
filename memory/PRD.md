# IngreLens Product Requirements

## Original problem statement
Use the github repository and the video(for front-end), complete camera and OCR integration, ai comparison with profile, and finish the food/med label scanner and rating giver app IngreLens, completely.

## Architecture decisions
- React/Vite frontend with a mobile-first app shell matching the supplied recording.
- FastAPI backend with SQLite persistence for accounts, profiles, and scan history in this repository.
- Browser camera capture with image upload and server-side Tesseract OCR fallback.
- Signed bearer sessions keep each user’s scans and health profile private to their account.

## User personas
- Health-conscious shoppers checking food ingredients and nutrition concerns.
- People checking medication directions, warnings, and expiry/safety reminders.

## Core requirements
- Account registration and login with backend-stored password hashes.
- Food and medicine scan modes, live camera, upload, paste text, OCR, personalized comparison, rating, history, and profile editing.

## Implemented (2026-08-24)
- Rebuilt the recording-inspired authentication, dashboard, scanner, results, history, and profile flows.
- Added camera capture, upload fallback, OCR processing, profile matching, safety scoring, medicine disclaimer, and persistent user-owned records.
- Added unique test IDs for user-facing controls and states.

## Prioritized backlog
- P0: Connect a production-grade medical/food knowledge model for richer label interpretation.
- P1: Add crop/retake editing controls after camera capture.
- P1: Add barcode lookup and structured nutrition facts extraction.
- P2: Add export/shareable scan reports and health-news management.