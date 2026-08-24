# IngreLens test credentials

Seed test account used by the testing agent:

- Email: `ingretest@ingrelens.dev`
- Password: `Password123!`

If the account does not exist yet, create it via `POST /api/auth/register`:

```bash
curl -X POST "$BASE/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"IngreLens QA","email":"ingretest@ingrelens.dev","password":"Password123!"}'
```

All protected endpoints require the bearer token returned by register/login:
- `GET /api/auth/me`
- `GET /api/profile` · `PUT /api/profile`
- `POST /api/scan`
- `GET /api/history` · `DELETE /api/history`

Backend base URL: read from `frontend/.env` → `REACT_APP_BACKEND_URL` (falls back to same-origin, ingress proxies `/api` to backend on port 8001).
