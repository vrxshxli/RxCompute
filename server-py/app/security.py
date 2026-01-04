from fastapi import Header, HTTPException
import jwt
from .config import APP_JWT_SECRET


def get_current_claims(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization[7:]
    try:
        payload = jwt.decode(token, APP_JWT_SECRET, algorithms=["HS256"])
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


def require_roles(allowed_roles: list[str]):
    def dep(claims = Header(None, convert_underscores=False)):
        # This inner dependency will actually be replaced by get_current_claims in router usage
        pass

    # FastAPI pattern: return a dependency function that checks roles using get_current_claims
    def dependency(authorization: str | None = Header(default=None)):
        claims = get_current_claims(authorization)
        role = claims.get("role", "user")
        if allowed_roles and role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden: insufficient role")
        return claims
    return dependency
