from datetime import datetime

from pydantic import Field

from src.app.schemas.base import CamelModel


class DepositResponse(CamelModel):
    id: str
    bank_name: str
    bank_color: str
    bank_text_color: str
    name: str
    rates: dict
    min_amount: int | None = None
    max_amount: int | None = None
    replenishment: bool
    withdrawal: bool
    freq: str
    is_systemic: bool
    conditions: list[str] | None = None
    tags: list[str] | None = None
    conditions_text: str | None = None
    params: str | None = None
    is_active: bool
    max_rate: float | None = None
    calc_income: float | None = None
    calc_total: float | None = None


class DepositCalculation(CamelModel):
    months: int
    rate: float
    income: float
    total_amount: float


class DepositChartPoint(CamelModel):
    months: int
    label: str
    max_rate: float


class DepositCommentResponse(CamelModel):
    id: int
    deposit_id: str
    user_id: str | None = None
    parent_id: int | None = None
    initials: str
    name: str
    text: str
    likes_count: int
    dislikes_count: int
    created_at: datetime


class DepositCommentCreate(CamelModel):
    text: str = Field(min_length=1, max_length=2000)
    parent_id: int | None = None
