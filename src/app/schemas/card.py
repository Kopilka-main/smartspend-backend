from datetime import datetime

from pydantic import Field

from src.app.schemas.base import CamelModel


class CardResponse(CamelModel):
    id: str
    bank_name: str
    bank_color: str
    bank_text_color: str
    name: str
    card_type: str
    cashback: dict | None = None
    cashback_note: str | None = None
    grace_days: int
    fee: int
    fee_base: int
    is_systemic: bool
    conditions: list[str] | None = None
    tags: list[str] | None = None
    bonus_type: str | None = None
    bonus_system: str | None = None
    bonus_desc: str | None = None
    fee_desc: str | None = None
    url: str | None = None
    is_active: bool


class UserCardResponse(CamelModel):
    id: int
    card_id: str
    spending: dict | None = None
    created_at: datetime


class UserCardCreate(CamelModel):
    card_id: str = Field(min_length=1, max_length=20)
    spending: dict | None = None


class CardCalculateRequest(CamelModel):
    spending: dict


class CardCalculateResponse(CamelModel):
    card_id: str
    card_name: str
    bank_name: str
    total_cashback: int
    breakdown: dict
