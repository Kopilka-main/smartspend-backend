import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import EmailStr, Field

from src.app.schemas.base import CamelModel


class RegisterRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)


class LoginRequest(CamelModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RefreshRequest(CamelModel):
    refresh_token: str


class TokenPair(CamelModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class UserFinanceInline(CamelModel):
    income: int = 0
    housing: int = 0
    credit: int = 0
    credit_months: int = 0
    capital: int = 0
    emo_rate: Decimal = Decimal("0.05")


class UserResponse(CamelModel):
    id: uuid.UUID
    email: str
    display_name: str
    username: str | None = None
    initials: str
    color: str
    bio: str | None = None
    avatar_url: str | None = None
    status: str
    theme: str
    joined_at: datetime
    followers_count: int = 0
    has_promo_setup: bool = False
    finance: UserFinanceInline | None = None


class AuthResponse(CamelModel):
    user: UserResponse
    tokens: TokenPair


class RefreshResponse(CamelModel):
    tokens: TokenPair


class ForgotPasswordRequest(CamelModel):
    email: EmailStr


class ResetPasswordRequest(CamelModel):
    token: str
    password: str = Field(min_length=8, max_length=128)


class ChangePasswordRequest(CamelModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)
