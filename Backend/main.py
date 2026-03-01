import os
import json
import tempfile
import logging

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import firebase_admin
from firebase_admin import credentials

from database import Base, engine
from migrate import migrate as run_migrations
from dependencies import get_current_user
from models.user import User
from saftery_policies_agents.ai_config import (
    LANGFUSE_ENABLED,
    LANGFUSE_HOST,
    LANGFUSE_PUBLIC_KEY,
    configure_langfuse_decorators,
    get_langfuse,
)
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
from routers import exception_agent_router
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

# Ensure @observe decorator runtime has Langfuse env values.
configure_langfuse_decorators()

logs_path = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(logs_path, exist_ok=True)
error_log_file = os.path.join(logs_path, "errors.log")
error_logger = logging.getLogger("rxcompute.errors")
if not error_logger.handlers:
    error_logger.setLevel(logging.ERROR)
    fh = logging.FileHandler(error_log_file, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    error_logger.addHandler(fh)
    error_logger.propagate = False

# CORS — support local web dashboard + deployed clients.
raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,https://rxcompute-web-main.onrender.com",
)
cors_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
# Always allow local dashboard/dev origins even if env var is misconfigured.
must_allow_origins = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
}
for _origin in must_allow_origins:
    if _origin not in cors_origins:
        cors_origins.append(_origin)
allow_any_origin = "*" in cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_any_origin else cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    # Browsers reject wildcard+credentials; keep credentials off for bearer-token API calls.
    allow_credentials=False if allow_any_origin else True,
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
app.include_router(exception_agent_router)
app.include_router(demand_forecast_router)

uploads_path = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")


@app.middleware("http")
async def _capture_unhandled_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:  # pragma: no cover
        error_logger.exception("Unhandled server error on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "RxCompute API", "version": "1.0.0"}


@app.get("/debug/error-logs", tags=["Debug"])
def debug_error_logs(
    lines: int = Query(80, ge=1, le=500),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    if not os.path.exists(error_log_file):
        return {"lines": [], "path": error_log_file}
    try:
        with open(error_log_file, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        tail = [ln.rstrip("\n") for ln in all_lines[-lines:]]
        return {"lines": tail, "path": error_log_file}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read error logs: {e}")


@app.get("/debug/langfuse-health", tags=["Debug"])
def debug_langfuse_health(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    masked_pk = ""
    if LANGFUSE_PUBLIC_KEY:
        masked_pk = f"{LANGFUSE_PUBLIC_KEY[:8]}...{LANGFUSE_PUBLIC_KEY[-6:]}"
    client_ok = False
    client_error = ""
    try:
        client = get_langfuse()
        client_ok = client is not None
    except Exception as exc:
        client_error = str(exc)
    return {
        "enabled": bool(LANGFUSE_ENABLED),
        "host": LANGFUSE_HOST,
        "public_key_masked": masked_pk,
        "client_initialized": client_ok,
        "client_error": client_error,
        "note": "If enabled=true and client_initialized=true but traces are missing, trigger an agent flow and check project/environment keys.",
    }