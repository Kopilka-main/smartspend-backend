from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from src.app.schemas.base import CamelModel
from src.app.schemas.user import AuthorInfo


class SetItemResponse(CamelModel):
    id: int
    name: str
    note: str | None = None
    qty: Decimal
    unit: str
    base_price: Decimal
    period_years: Decimal
    item_type: str
    monthly_cost: Decimal = Decimal("0")


class SetItemCreate(CamelModel):
    name: str = Field(min_length=1, max_length=200)
    note: str | None = Field(None, max_length=200)
    qty: Decimal = Field(gt=0)
    unit: str = Field(default="шт", max_length=20)
    base_price: Decimal = Field(gt=0)
    period_years: Decimal = Field(gt=0)
    item_type: str = Field(default="consumable")


class SetResponse(CamelModel):
    id: str
    source: str
    category_id: str
    set_type: str
    color: str
    title: str
    description: str | None = None
    amount: int | None = None
    amount_label: str | None = None
    users_count: int
    added: date | None = None
    is_private: bool
    hidden: bool = False
    about_title: str | None = None
    about_text: str | None = None
    items: list[SetItemResponse] = []
    author: AuthorInfo | None = None
    created_at: datetime
    updated_at: datetime


class SetListItem(CamelModel):
    id: str
    source: str
    category_id: str
    set_type: str
    color: str
    title: str
    description: str | None = None
    amount: int | None = None
    amount_label: str | None = None
    users_count: int
    is_private: bool
    items_count: int = 0
    author: AuthorInfo | None = None
    created_at: datetime


class SetCreate(CamelModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    category_id: str = Field(min_length=1, max_length=20)
    set_type: str = Field(default="base", max_length=20)
    color: str = Field(default="#8DBFA8", max_length=7)
    is_private: bool = False
    about_title: str | None = Field(None, max_length=200)
    about_text: str | None = None
    items: list[SetItemCreate] = []


class SetUpdate(CamelModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    about_title: str | None = Field(None, max_length=200)
    about_text: str | None = None
    items: list[SetItemCreate] | None = None


class SetCommentResponse(CamelModel):
    id: int
    set_id: str
    user_id: str | None = None
    initials: str
    name: str
    text: str
    likes_count: int
    dislikes_count: int
    created_at: datetime


class SetCommentCreate(CamelModel):
    text: str = Field(min_length=1, max_length=2000)
