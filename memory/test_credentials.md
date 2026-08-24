# IngreLens test credentials

No seeded account is created. Register a test account through `/api/auth/register` with any email and a password of at least 8 characters.

Protected endpoints use the bearer token returned by register/login:
- GET `/api/auth/me`
- GET/PUT `/api/profile`
- POST `/api/scan`
- GET/DELETE `/api/history`