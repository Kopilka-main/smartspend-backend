from datetime import datetime

from src.app.schemas.base import CamelModel


class CompanyResponse(CamelModel):
    id: str
    name: str
    abbr: str | None = None
    color: str
    category_id: str | None = None
    category_name: str | None = None
    description: str | None = None
    promo_types: list[str] | None = None


class UserCompanyResponse(CamelModel):
    id: int
    company_id: str
    category_id: str | None = None
    created_at: datetime


class BatchCompaniesRequest(CamelModel):
    company_ids: list[str]
