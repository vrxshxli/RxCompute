import os
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials

from database import Base, engine
from routers import (
    auth_router,
    users_router,
    medicines_router,
    orders_router,
    notifications_router,
)

# ─── Initialize Firebase Admin SDK ────────────────────────
if not firebase_admin._apps:
    # Option 1: GOOGLE_APPLICATION_CREDENTIALS env var (file path)
    # Option 2: FIREBASE_SERVICE_ACCOUNT env var (JSON string — best for Render)
    firebase_sa = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if firebase_sa:
        cred = credentials.Certificate(json.loads(firebase_sa))
        firebase_admin.initialize_app(cred)
    elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        firebase_admin.initialize_app()
    else:
        # Default init (works in GCP environments)
        firebase_admin.initialize_app()

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RxCompute API",
    description="AI-Powered Pharmacy Management System — Backend API",
    version="1.0.0",
)

# CORS — allow Flutter app on any origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(medicines_router)
app.include_router(orders_router)
app.include_router(notifications_router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "RxCompute API", "version": "1.0.0"}
