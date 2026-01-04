# Auth Backends: Express.js and FastAPI with PostgreSQL + Firebase (Google + Phone OTP)

This repo contains two minimal auth backends that rely on Firebase Authentication for identity (Google Sign-In, Phone OTP, Email/Password) and then issue an application JWT after storing the user in PostgreSQL.

- server-node: Express.js implementation
- server-py: FastAPI implementation

Both expose the same core endpoints:
- POST /auth/verify: Accepts a Firebase ID token (`idToken`) from the client, verifies it using Firebase Admin, upserts the user into Postgres, and returns an app JWT + user row.
- GET /auth/me: Reads `Authorization: Bearer <app-jwt>` and returns decoded payload.
- GET /health: Healthcheck.

## 1) PostgreSQL schema
Apply once:

```
psql "$DATABASE_URL" -f server-node/sql/schema.sql
```

Table: `users(uid unique, email, phone, name, photo_url, provider, timestamps)`.

## 2) Firebase setup (Google + Phone)
- Create Firebase project in Console.
- Enable Authentication providers: Google and Phone.
- For Phone, add test phone numbers or set up a real phone number flow.
- Generate a Service Account key (Role: Firebase Admin SDK Service Agent). Download JSON.
- Backend credentials options:
  - Set env `FIREBASE_SERVICE_ACCOUNT_JSON` to the entire JSON content (one line).
  - Or set `GOOGLE_APPLICATION_CREDENTIALS` to the JSON file path.

Client workflow to obtain `idToken`:
- Google: use `signInWithPopup` or `signInWithRedirect`, then call `getIdToken()` on the Firebase user.
- Phone: verify phone + OTP with `signInWithPhoneNumber`, then `confirmationResult.confirm(code)`, then `getIdToken()`.
- Email/Password: `createUserWithEmailAndPassword` then `getIdToken()`.

Send that `idToken` to your backend `/auth/verify`.

## 3) Node (Express.js)

- Copy `.env.example` to `.env` in `server-node/` and fill values.
- Install and run:
```
cd server-node
npm i
npm run dev
```

Endpoints:
- POST http://localhost:4000/auth/verify
  Body JSON: `{ "idToken": "<firebase id token>", "displayName": "optional", "photoURL": "optional" }`
- GET http://localhost:4000/auth/me with header `Authorization: Bearer <app jwt>`

## 4) Python (FastAPI)

- Copy `.env.example` to `.env` in `server-py/` and fill values.
- Install and run:
```
cd server-py
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Endpoints:
- POST http://localhost:8000/auth/verify
- GET http://localhost:8000/auth/me

## 5) Step-by-step Signup/Login Flow
- Client performs identity with Firebase (Google/Phone/Email).
- Client obtains Firebase ID token via SDK.
- Client sends `idToken` to your backend `/auth/verify`.
- Backend verifies token via Firebase Admin.
- Backend upserts user to Postgres (`users` table).
- Backend issues application JWT (HS256) and returns `{ token, user }`.
- Client stores app JWT (e.g., httpOnly cookie or memory/localStorage depending on needs).
- For authenticated routes, client includes `Authorization: Bearer <token>`.

## Notes
- Do not send Firebase ID tokens directly to other services; only to your backend.
- Rotate `APP_JWT_SECRET` in production and keep it safe.
- Consider adding refresh tokens, roles/permissions, and rate limiting for production.
