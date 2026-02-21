from pydantic import BaseModel


class SendOtpRequest(BaseModel):
    phone: str


class VerifyOtpRequest(BaseModel):
    phone: str
    otp: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    is_registered: bool
