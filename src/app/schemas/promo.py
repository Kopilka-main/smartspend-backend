from datetime import datetime

from pydantic import Field

from src.app.schemas.base import CamelModel
from src.app.schemas.company import CompanyResponse


class PromoResponse(CamelModel):
    id: int
    type: str
    company_id: str | None = None
    category_id: str | None = None
    author_id: str | None = None
    text: str
    channel: str | None = None
    url: str | None = None
    conditions: list[str] | None = None
    expires_at: datetime | None = None
    votes_up: int
    votes_down: int
    is_active: bool
    created_at: datetime
    company: CompanyResponse | None = None


class PromoCreate(CamelModel):
    type: str = Field(default="whisper", pattern=r"^whisper$")
    company_id: str | None = None
    category_id: str | None = None
    text: str = Field(min_length=1, max_length=5000)
    conditions: list[str] | None = None
    expires_at: datetime | None = None


class PromoVoteRequest(CamelModel):
    vote: str = Field(pattern=r"^(up|down)$")


class PromoCommentResponse(CamelModel):
    id: int
    promo_id: int
    user_id: str | None = None
    parent_id: int | None = None
    initials: str
    name: str
    text: str
    likes_count: int
    dislikes_count: int
    created_at: datetime


class PromoCommentCreate(CamelModel):
    text: str = Field(min_length=1, max_length=2000)
    parent_id: int | None = None
