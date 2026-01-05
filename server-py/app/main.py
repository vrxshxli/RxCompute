from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.auth import router as auth_router
from app.dashboard import router as dashboard_router
from app.dashboard_user import router as user_dashboard_router

app = FastAPI(title="PharmaForge Auth API (FastAPI)")

# CORS configuration (env-driven)
# Set ALLOWED_ORIGINS as a comma-separated list in production, e.g.:
# ALLOWED_ORIGINS=https://yourapp.vercel.app,https://pharmaforge-api.onrender.com
allowed_origins_env = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://192.168.220.1:5173,https://invaders-pharmaforge-ai-2.onrender.com, https://invaders-pharmaforge-ai.onrender.com"
).strip()
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/health')
async def health():
    return {"ok": True, "service": "pharmaforge-auth-py"}

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(user_dashboard_router)