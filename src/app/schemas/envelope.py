from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from src.app.schemas.base import CamelModel


class EnvelopeCategoryResponse(CamelModel):
    id: str
    name: str
    color: str


class EnvelopeItemResponse(CamelModel):
    id: str
    name: str
    item_type: str
    price: int = 0
    qty: Decimal | None = None
    unit: str | None = None
    daily_use: Decimal | None = None
    wear_life_weeks: int | None = None
    purchase_date: date | None = None
    paused: bool = False
    base_price: int | None = None
    period_years: Decimal | None = None


class EnvelopeResponse(CamelModel):
    id: int
    user_id: str
    category_id: str
    set_id: str
    name: str
    items_count: int
    amount: int
    envelope_type: str
    source: str | None = None
    period: str | None = None
    paused: bool = False
    scale: Decimal = Decimal("1.00")
    items: list[EnvelopeItemResponse] = []
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_obj(
        cls,
        e,
        source: str | None = None,
        paused: bool = False,
        items: list[EnvelopeItemResponse] | None = None,
    ) -> "EnvelopeResponse":
        return cls(
            id=e.id,
            user_id=str(e.user_id),
            category_id=e.category_id,
            set_id=e.set_id,
            name=e.name,
            items_count=e.items_count,
            amount=e.amount,
            envelope_type=e.envelope_type,
            source=source,
            period=e.period,
            paused=paused,
            scale=e.scale if e.scale is not None else Decimal("1.00"),
            items=items or [],
            created_at=e.created_at,
            updated_at=e.updated_at,
        )


class EnvelopeCreate(CamelModel):
    category_id: str = Field(min_length=1, max_length=20)
    set_id: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=200)
    items_count: int = Field(ge=0, default=0)
    amount: int = Field(ge=0, default=0)
    envelope_type: str = Field(default="consumable", max_length=30)
    period: str | None = Field(None, max_length=50)
