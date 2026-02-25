import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt
from firebase_admin import auth as firebase_auth

from database import get_db
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from models.user import User, OTP
from schemas.auth import (
    SendOtpRequest,
    VerifyOtpRequest,
    GoogleAuthRequest,
    TokenResponse,
    WebLoginRequest,
)
from services.security import verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])
VALID_WEB_ROLES = {"admin", "pharmacy_store", "warehouse", "user"}
ROLE_ALIASES = {"pharmacy": "pharmacy_store"}


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _normalize_role(role: str | None) -> str:
    raw = (role or "user").strip().lower()
    return ROLE_ALIASES.get(raw, raw)


# ─── Google Sign-In via Firebase ───────────────────────────
@router.post("/google", response_model=TokenResponse)
def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Verify Firebase ID token and return a backend JWT."""
    try:
        # Verify the Firebase ID token
        decoded_token = firebase_auth.verify_id_token(req.id_token)
        firebase_uid = decoded_token["uid"]
        email = decoded_token.get("email")
        name = decoded_token.get("name")
        picture = decoded_token.get("picture")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token",
        )

    # Find user by google_id (stores firebase_uid) or email
    user = db.query(User).filter(User.google_id == firebase_uid).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()

    if user:
        # Update info if missing
        if not user.google_id:
            user.google_id = firebase_uid
        if not user.profile_picture and picture:
            user.profile_picture = picture
        if not user.name and name:
            user.name = name
        if not user.email and email:
            user.email = email
        user.is_verified = True
        user.role = user.role or "user"
    else:
        # Create new user
        user = User(
            google_id=firebase_uid,
            email=email,
            name=name,
            profile_picture=picture,
            is_verified=True,
            is_registered=False,
            role="user",
        )
        db.add(user)

    db.commit()

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        is_registered=user.is_registered,
        role=user.role,
        name=user.name,
        email=user.email,
        profile_picture=user.profile_picture,
    )


# ─── OTP Login (secondary) ────────────────────────────────
@router.post("/send-otp")
def send_otp(req: SendOtpRequest, db: Session = Depends(get_db)):
    """Generate a 6-digit OTP for the given phone number."""
    otp_code = str(random.randint(100000, 999999))

    db.query(OTP).filter(OTP.phone == req.phone).delete()
    db.add(OTP(phone=req.phone, otp=otp_code))
    db.commit()

    return {"message": "OTP sent", "mock_otp": otp_code}


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(req: VerifyOtpRequest, db: Session = Depends(get_db)):
    """Verify OTP and return a JWT access token."""
    record = (
        db.query(OTP)
        .filter(OTP.phone == req.phone, OTP.otp == req.otp)
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP",
        )

    db.query(OTP).filter(OTP.phone == req.phone).delete()

    user = db.query(User).filter(User.phone == req.phone).first()
    if not user:
        user = User(phone=req.phone, is_verified=True, role="user")
        db.add(user)
        db.flush()
    else:
        user.is_verified = True
        user.role = user.role or "user"

    db.commit()

    token = create_access_token({"sub": str(user.id), "phone": user.phone, "role": user.role})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        is_registered=user.is_registered,
        role=user.role,
        name=user.name,
        email=user.email,
        profile_picture=user.profile_picture,
    )


@router.post("/web-login", response_model=TokenResponse)
def web_login(req: WebLoginRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    role = _normalize_role(req.role)
    if role not in VALID_WEB_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if user.role != role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role mismatch. This account belongs to '{user.role}'",
        )
    if role == "admin" and not (user.name or "").strip():
        user.name = "Admin"
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        is_registered=user.is_registered,
        role=user.role,
        name=user.name,
        email=user.email,
        profile_picture=user.profile_picture,
    )
