from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from src.app.schemas.base import CamelModel


class InventoryPurchaseResponse(CamelModel):
    id: int
    position: int
    bought: bool
    purchase_date: date | None = None


class InventoryPhotoResponse(CamelModel):
    id: int
    url: str
    file_name: str
    created_at: datetime


class InventoryItemResponse(CamelModel):
    id: str
    user_id: str
    group_id: str
    group_name: str | None = None
    type: str
    name: str
    price: int
    set_id: str | None = None
    set_name: str | None = None
    is_extra: bool
    paused: bool
    notes: str | None = None
    qty: Decimal | None = None
    unit: str | None = None
    daily_use: Decimal | None = None
    last_bought: date | None = None
    wear_life_weeks: int | None = None
    wear_life: int | None = None
    wear_life_unit: str | None = None
    use_rate: Decimal | None = None
    use_period: str | None = None
    purchase_date: date | None = None
    status: str = "ok"
    remaining_qty: Decimal | None = None
    remaining_percent: int | None = None
    remaining_days: int | None = None
    monthly_cost: int = 0
    weekly_cost: int = 0
    monthly_need: Decimal | None = None
    price_per_unit: Decimal | None = None
    residual_percent: int | None = None
    residual_value: int | None = None
    purchases: list[InventoryPurchaseResponse] = []
    photos: list[InventoryPhotoResponse] = []
    created_at: datetime
    updated_at: datetime


class InventoryItemCreate(CamelModel):
    group_id: str = Field(max_length=5)
    type: str = Field(max_length=20)
    name: str = Field(min_length=1, max_length=200)
    price: int = Field(ge=0)
    set_id: str | None = None
    notes: str | None = None
    qty: Decimal | None = Field(None, ge=0)
    unit: str | None = Field(None, max_length=20)
    daily_use: Decimal | None = Field(None, gt=0)
    last_bought: date | None = None
    wear_life_weeks: int | None = Field(None, gt=0)
    wear_life: int | None = Field(None, gt=0)
    wear_life_unit: str | None = Field(None, max_length=10)
    use_rate: Decimal | None = Field(None, gt=0)
    use_period: str | None = Field(None, max_length=10)
    purchase_date: date | None = None


class InventoryItemUpdate(CamelModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    price: int | None = Field(None, ge=0)
    notes: str | None = None
    qty: Decimal | None = Field(None, ge=0)
    unit: str | None = Field(None, max_length=20)
    daily_use: Decimal | None = Field(None, gt=0)
    last_bought: date | None = None
    wear_life_weeks: int | None = Field(None, gt=0)
    wear_life: int | None = Field(None, gt=0)
    wear_life_unit: str | None = Field(None, max_length=10)
    use_rate: Decimal | None = Field(None, gt=0)
    use_period: str | None = Field(None, max_length=10)
    purchase_date: date | None = None
    paused: bool | None = None


class ActivateItemRequest(CamelModel):
    purchase_date: date | None = None
    qty: Decimal | None = Field(None, gt=0)
    price: int | None = Field(None, ge=0)


class RestockRequest(CamelModel):
    qty_added: Decimal = Field(gt=0)


class ReplaceRequest(CamelModel):
    purchase_date: date


class ReassignSetRequest(CamelModel):
    set_id: str = Field(min_length=1, max_length=20)


class InventoryGroupResponse(CamelModel):
    id: str
    name: str
    color: str
    items: list[InventoryItemResponse] = []
