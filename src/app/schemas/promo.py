from datetime import datetime

from pydantic import Field

from src.app.schemas.base import CamelModel
from src.app.schemas.company import CompanyResponse
from src.app.schemas.user import AuthorInfo


class PromoVoteEntry(CamelModel):
    user_id: str
    vote: str
    created_at: datetime


class PromoResponse(CamelModel):
    id: int
    type: str
    company_id: str | None = None
    category_id: str | None = None
    category_name: str | None = None
    author_id: str | None = None
    author: AuthorInfo | None = None
    title: str | None = None
    text: str
    code: str | None = None
    channel: str | None = None
    url: str | None = None
    source_url: str | None = None
    promo_filter: str | None = None
    conditions: list[str] | None = None
    expires_at: datetime | None = None
    votes_up: int
    votes_down: int
    comments_count: int = 0
    my_vote: str | None = None
    vote_history: list[PromoVoteEntry] = []
    is_active: bool
    created_at: datetime
    company: CompanyResponse | None = None


class PromoCreate(CamelModel):
    type: str = Field(default="whisper", pattern=r"^(whisper|broadcast|event|coupon)$")
    company_id: str | None = None
    category_id: str | None = None
    title: str | None = Field(None, max_length=300)
    text: str = Field(min_length=1, max_length=5000)
    code: str | None = Field(None, max_length=100)
    source_url: str | None = None
    channel: str | None = Field(None, max_length=50)
    promo_filter: str | None = Field(None, max_length=30)
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
