from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .auth import router as auth_router
from .dashboard import router as dashboard_router
from .dashboard_user import router as user_dashboard_router

app = FastAPI(title="PharmaForge Auth API (FastAPI)")

# Enable permissive CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
