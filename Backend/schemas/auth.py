from pydantic import BaseModel


class SendOtpRequest(BaseModel):
    phone: str


class VerifyOtpRequest(BaseModel):
    phone: str
    otp: str


class GoogleAuthRequest(BaseModel):
    id_token: str


class WebLoginRequest(BaseModel):
    email: str
    password: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    is_registered: bool
    role: str = "user"
    name: str | None = None
    email: str | None = None
    profile_picture: str | None = None