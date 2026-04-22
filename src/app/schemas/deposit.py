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


class DepositCalculation(CamelModel):
    months: int
    rate: float
    income: float
    total_amount: float
