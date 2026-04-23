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
    income: int | None = Field(None, ge=0)
    housing: int | None = Field(None, ge=0)
    credit: int | None = Field(None, ge=0)
    credit_months: int | None = Field(None, ge=0)
    capital: int | None = Field(None, ge=0)
    emo_rate: Decimal | None = Field(None, ge=Decimal("0.03"), le=Decimal("0.10"))


class ProfileUpdate(CamelModel):
    display_name: str | None = Field(None, min_length=1, max_length=100)
    username: str | None = Field(None, min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    bio: str | None = Field(None, max_length=500)


class SettingsUpdate(CamelModel):
    theme: str | None = None
    timezone: str | None = Field(None, max_length=50)
    location: str | None = Field(None, max_length=100)
    notify_new_sets: bool | None = None
    notify_author_articles: bool | None = None
    notify_subscriptions: bool | None = None
    notify_set_changes: bool | None = None
    notify_reminders: bool | None = None
    privacy_sets: str | None = Field(None, pattern=r"^(all|followers|me)$")
    privacy_articles: str | None = Field(None, pattern=r"^(all|followers|me)$")
    privacy_profile: str | None = Field(None, pattern=r"^(all|followers|me)$")


class SettingsResponse(CamelModel):
    theme: str
    timezone: str
    location: str | None = None
    notify_new_sets: bool
    notify_author_articles: bool
    notify_subscriptions: bool
    notify_set_changes: bool
    notify_reminders: bool
    privacy_sets: str
    privacy_articles: str
    privacy_profile: str


class AuthorInfo(CamelModel):
    id: uuid.UUID
    display_name: str
    username: str | None = None
    initials: str
    color: str
    avatar_url: str | None = None


class UserPublicResponse(CamelModel):
    id: uuid.UUID
    display_name: str
    username: str | None = None
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
