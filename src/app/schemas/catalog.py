from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from src.app.schemas.base import CamelModel
from src.app.schemas.user import AuthorInfo


class SetItemResponse(CamelModel):
    id: int
    name: str
    note: str | None = None
    item_type: str
    price: int = 0
    qty: Decimal | None = None
    unit: str | None = None
    daily_use: Decimal | None = None
    wear_life_weeks: int | None = None
    purchase_date: date | None = None
    planned_price: int | None = None
    base_price: Decimal | None = None
    period_years: Decimal | None = None
    monthly_cost: Decimal = Decimal("0")


class SetItemCreate(CamelModel):
    name: str = Field(min_length=1, max_length=200)
    note: str | None = Field(None, max_length=200)
    item_type: str = Field(default="consumable")
    price: int = Field(default=0, ge=0)
    qty: Decimal | None = Field(None, gt=0)
    unit: str | None = Field(None, max_length=20)
    daily_use: Decimal | None = Field(None, gt=0)
    wear_life_weeks: int | None = Field(None, gt=0)
    purchase_date: date | None = None
    planned_price: int | None = Field(None, ge=0)
    base_price: Decimal | None = Field(None, gt=0)
    period_years: Decimal | None = Field(None, gt=0)


class SetPhotoResponse(CamelModel):
    id: int
    url: str
    file_name: str
    position: int = 0
    created_at: datetime


class SetResponse(CamelModel):
    id: str
    source: str
    category_id: str
    category_name: str | None = None
    set_type: str
    color: str
    title: str
    description: str | None = None
    amount: int | None = None
    amount_label: str | None = None
    monthly: int | None = None
    full_cost: int | None = None
    period: str | None = None
    users_count: int
    comments_count: int = 0
    likes_count: int = 0
    dislikes_count: int = 0
    added: date | None = None
    is_private: bool
    hidden: bool = False
    status: str = "published"
    about_title: str | None = None
    about_text: str | None = None
    items: list[SetItemResponse] = []
    photos: list[SetPhotoResponse] = []
    author: AuthorInfo | None = None
    created_at: datetime
    updated_at: datetime


class SetListItem(CamelModel):
    id: str
    source: str
    category_id: str
    category_name: str | None = None
    set_type: str
    color: str
    title: str
    description: str | None = None
    amount: int | None = None
    amount_label: str | None = None
    monthly: int | None = None
    full_cost: int | None = None
    period: str | None = None
    users_count: int
    comments_count: int = 0
    likes_count: int = 0
    dislikes_count: int = 0
    is_private: bool
    items_count: int = 0
    items: list[SetItemResponse] = []
    author: AuthorInfo | None = None
    created_at: datetime


class SetCreate(CamelModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    category_id: str = Field(min_length=1, max_length=20)
    set_type: str = Field(default="base", max_length=20)
    color: str = Field(default="#8DBFA8", max_length=7)
    is_private: bool = False
    status: str = Field(default="published", max_length=20)
    period: str | None = Field(None, max_length=50)
    full_cost: int | None = Field(None, ge=0)
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
    parent_id: int | None = None
    initials: str
    name: str
    text: str
    likes_count: int
    dislikes_count: int
    created_at: datetime


class SetCommentCreate(CamelModel):
    text: str = Field(min_length=1, max_length=2000)
    parent_id: int | None = None
