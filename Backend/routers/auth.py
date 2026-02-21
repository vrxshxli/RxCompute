import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt

from database import get_db
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from models.user import User, OTP
from schemas.auth import SendOtpRequest, VerifyOtpRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/send-otp")
def send_otp(req: SendOtpRequest, db: Session = Depends(get_db)):
    """Generate a 6-digit OTP for the given phone number."""
    otp_code = str(random.randint(100000, 999999))

    # Remove previous OTPs for this phone
    db.query(OTP).filter(OTP.phone == req.phone).delete()
    db.add(OTP(phone=req.phone, otp=otp_code))
    db.commit()

    # In production, send OTP via SMS gateway
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

    # Clean up used OTP
    db.query(OTP).filter(OTP.phone == req.phone).delete()

    # Get or create user
    user = db.query(User).filter(User.phone == req.phone).first()
    if not user:
        user = User(phone=req.phone, is_verified=True)
        db.add(user)
    else:
        user.is_verified = True

    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "phone": user.phone})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        is_registered=user.is_registered,
    )
