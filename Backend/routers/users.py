from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from schemas.user import UserRegister, UserUpdate, UserOut

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=UserOut)
def register_user(
    data: UserRegister,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Complete user registration after OTP verification."""
    current_user.name = data.name
    current_user.age = data.age
    current_user.gender = data.gender
    current_user.email = data.email
    current_user.allergies = data.allergies
    current_user.conditions = data.conditions
    current_user.is_registered = True
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    """Return current user profile."""
    return current_user


@router.put("/me", response_model=UserOut)
def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user profile fields."""
    update_data = data.model_dump(exclude_unset=True)
    if "role" in update_data and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can change user role")
    for key, value in update_data.items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return current_user
