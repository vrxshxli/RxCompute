import os
import json
import tempfile

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import firebase_admin
from firebase_admin import credentials

from database import Base, engine
from migrate import migrate as run_migrations
from routers import (
    auth_router,
    users_router,
    medicines_router,
    orders_router,
    notifications_router,
    user_medications_router,
    home_router,
    chat_router,
    jobs_router,
    webhooks_router,
    pharmacy_stores_router,
    warehouse_router,
    safety_router,
    scheduler_router,
)

from routers import predictions_router
from routers import order_agent_router
from routers import exceptions_router
from routers import demand_forecast_router


# ─── Initialize Firebase Admin SDK ────────────────────────
if not firebase_admin._apps:
    firebase_sa = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if firebase_sa:
        try:
            # Try parsing directly
            sa_dict = json.loads(firebase_sa)
        except json.JSONDecodeError:
            # Render sometimes adds extra quotes — strip them
            cleaned = firebase_sa.strip().strip("'").strip('"')
            try:
                sa_dict = json.loads(cleaned)
            except json.JSONDecodeError:
                # Last resort: write to temp file and use file path
                print("⚠ Could not parse FIREBASE_SERVICE_ACCOUNT as JSON, writing to temp file...")
                tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
                tmp.write(firebase_sa)
                tmp.close()
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name
                firebase_admin.initialize_app()
                sa_dict = None

        if sa_dict is not None:
            # Fix escaped newlines in private_key (common Render issue)
            if "private_key" in sa_dict and "\\n" in sa_dict["private_key"]:
                sa_dict["private_key"] = sa_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(sa_dict)
            firebase_admin.initialize_app(cred)
        print("✓ Firebase Admin SDK initialized")
    else:
        print("⚠ FIREBASE_SERVICE_ACCOUNT not set — Google Sign-In will not work")
        try:
            firebase_admin.initialize_app()
        except Exception:
            pass

# Create all tables
Base.metadata.create_all(bind=engine)
try:
    run_migrations()
except Exception as e:
    print(f"⚠ Migration warning at startup: {e}")

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
app.include_router(user_medications_router)
app.include_router(home_router)
app.include_router(chat_router)
app.include_router(jobs_router)
app.include_router(webhooks_router)
app.include_router(pharmacy_stores_router)
app.include_router(warehouse_router)
app.include_router(safety_router)
app.include_router(scheduler_router)
app.include_router(predictions_router)
app.include_router(order_agent_router)
app.include_router(exceptions_router)
app.include_router(demand_forecast_router)

uploads_path = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "RxCompute API", "version": "1.0.0"}
A