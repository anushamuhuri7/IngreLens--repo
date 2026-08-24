# IngreLens authentication testing

1. Register with `POST /api/auth/register` using name, email, and an 8+ character password.
2. Save the returned token and send it as `Authorization: Bearer <token>`.
3. Confirm `/api/auth/me` returns only the signed-in user.
4. Confirm profile updates and history are isolated to that user.
5. Confirm an incorrect password returns 401 and duplicate email returns 409.