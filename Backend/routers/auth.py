import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt
from firebase_admin import auth as firebase_auth

from database import get_db
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from models.user import User, OTP
from schemas.auth import SendOtpRequest, VerifyOtpRequest, GoogleAuthRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


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
    else:
        # Create new user
        user = User(
            google_id=firebase_uid,
            email=email,
            name=name,
            profile_picture=picture,
            is_verified=True,
            is_registered=False,
        )
        db.add(user)

    db.commit()

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        is_registered=user.is_registered,
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
        user = User(phone=req.phone, is_verified=True)
        db.add(user)
        db.flush()
    else:
        user.is_verified = True

    db.commit()

    token = create_access_token({"sub": str(user.id), "phone": user.phone})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        is_registered=user.is_registered,
        name=user.name,
        email=user.email,
        profile_picture=user.profile_picture,
    )
