from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
import jwt
from .firebase import verify_id_token
from .db import upsert_user, update_user_role
from .config import APP_JWT_SECRET
from .security import get_current_claims, require_roles

router = APIRouter(prefix="/auth", tags=["auth"])

class VerifyBody(BaseModel):
    idToken: str
    displayName: str | None = None
    photoURL: str | None = None


def sign_app_token(user):
    payload = {"sub": user["uid"], "uid": user["uid"], "id": user["id"], "role": user.get("role", "user")}
    token = jwt.encode(payload, APP_JWT_SECRET, algorithm="HS256")
    return token


@router.post('/verify')
async def verify(body: VerifyBody):
    try:
        decoded = verify_id_token(body.idToken)
        user = upsert_user(
            uid=decoded.get('uid'),
            email=decoded.get('email'),
            phone=decoded.get('phone_number'),
            name=decoded.get('name') or body.displayName,
            photo_url=decoded.get('picture') or body.photoURL,
            provider=(decoded.get('firebase') or {}).get('sign_in_provider', 'unknown'),
        )
        token = sign_app_token(user)
        return {"token": token, "user": user}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get('/me')
async def me(authorization: str | None = Header(default=None)):
    try:
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(status_code=401, detail='Missing bearer token')
        token = authorization[7:]
        payload = jwt.decode(token, APP_JWT_SECRET, algorithms=["HS256"])
        return {"ok": True, "auth": payload}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


class LoginBody(BaseModel):
    idToken: str


@router.post('/login')
async def login(body: LoginBody):
    # Login mirrors verify: trust Firebase for identity, issue our JWT
    try:
        decoded = verify_id_token(body.idToken)
        user = upsert_user(
            uid=decoded.get('uid'),
            email=decoded.get('email'),
            phone=decoded.get('phone_number'),
            name=decoded.get('name'),
            photo_url=decoded.get('picture'),
            provider=(decoded.get('firebase') or {}).get('sign_in_provider', 'unknown'),
        )
        token = sign_app_token(user)
        return {"token": token, "user": user}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


class RoleUpdateBody(BaseModel):
    uid: str
    role: str


@router.post('/role')
async def set_role(body: RoleUpdateBody, claims=Depends(require_roles(["admin"]))):
    # Only admins can change roles
    allowed = {"user", "warehouse", "admin", "pharmacist"}
    if body.role not in allowed:
        raise HTTPException(status_code=400, detail="Invalid role")
    updated = update_user_role(body.uid, body.role)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True, "user": updated}
