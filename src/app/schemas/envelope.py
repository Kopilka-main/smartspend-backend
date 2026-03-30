from datetime import datetime

from pydantic import Field

from src.app.schemas.base import CamelModel


class EnvelopeCategoryResponse(CamelModel):
    id: str
    name: str
    color: str


class EnvelopeResponse(CamelModel):
    id: int
    user_id: str
    category_id: str
    set_id: str
    name: str
    items_count: int
    amount: int
    envelope_type: str
    period: str | None = None
    created_at: datetime
    updated_at: datetime


class EnvelopeCreate(CamelModel):
    category_id: str = Field(min_length=1, max_length=20)
    set_id: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=200)
    items_count: int = Field(ge=0, default=0)
    amount: int = Field(ge=0, default=0)
    envelope_type: str = Field(default="consumable", max_length=30)
    period: str | None = Field(None, max_length=50)
