from fastapi import APIRouter, Depends
from .security import get_current_claims, require_roles

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("")
async def dashboard_home(claims = Depends(get_current_claims)):
    # Visible to any authenticated user
    return {
        "message": "Welcome to the dashboard",
        "uid": claims.get("uid"),
        "role": claims.get("role", "user"),
    }

@router.get("/user")
async def user_area(claims = Depends(require_roles(["user","admin","pharmacist","warehouse"]))):
    return {"area": "user", "role": claims.get("role")}

@router.get("/warehouse")
async def warehouse_area(claims = Depends(require_roles(["warehouse","admin"]))):
    return {"area": "warehouse", "role": claims.get("role")}

@router.get("/pharmacist")
async def pharmacist_area(claims = Depends(require_roles(["pharmacist","admin"]))):
    return {"area": "pharmacist", "role": claims.get("role")}

@router.get("/admin")
async def admin_area(claims = Depends(require_roles(["admin"]))):
    return {"area": "admin", "role": claims.get("role")}
