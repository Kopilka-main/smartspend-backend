import uuid
from datetime import datetime

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


class UserResponse(CamelModel):
    id: uuid.UUID
    email: str
    display_name: str
    initials: str
    color: str
    bio: str | None = None
    avatar_url: str | None = None
    status: str
    theme: str
    sidebar_collapsed: bool
    joined_at: datetime


class AuthResponse(CamelModel):
    user: UserResponse
    tokens: TokenPair


class RefreshResponse(CamelModel):
    tokens: TokenPair
