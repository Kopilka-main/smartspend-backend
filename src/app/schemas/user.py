import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import Field

from src.app.schemas.base import CamelModel


class UserFinanceResponse(CamelModel):
    income: int
    housing: int
    credit: int
    credit_months: int
    capital: int
    emo_rate: Decimal
    updated_at: datetime


class UserFinanceUpdate(CamelModel):
    income: int = Field(ge=0)
    housing: int = Field(ge=0)
    credit: int = Field(ge=0)
    credit_months: int = Field(ge=0)
    capital: int = Field(ge=0)
    emo_rate: Decimal = Field(ge=Decimal("0.03"), le=Decimal("0.10"))


class ProfileUpdate(CamelModel):
    display_name: str | None = Field(None, min_length=1, max_length=100)
    bio: str | None = Field(None, max_length=500)


class SettingsUpdate(CamelModel):
    theme: str | None = None
    sidebar_collapsed: bool | None = None


class AuthorInfo(CamelModel):
    id: uuid.UUID
    display_name: str
    initials: str
    color: str
    avatar_url: str | None = None


class UserPublicResponse(CamelModel):
    id: uuid.UUID
    display_name: str
    initials: str
    color: str
    bio: str | None = None
    avatar_url: str | None = None
    joined_at: datetime
    followers_count: int = 0
    following_count: int = 0
    articles_count: int = 0
    sets_count: int = 0
    is_following: bool = False


class ProfileSummary(CamelModel):
    income: int
    housing: int
    credit: int
    credit_months: int
    capital: int
    emo_rate: Decimal
    smart_base: int
    emo_spend: int
    free_remainder: int
    capital_growth_monthly: int


class DeleteAccountRequest(CamelModel):
    password: str = Field(min_length=1)
