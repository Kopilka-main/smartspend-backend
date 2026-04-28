import uuid

from fastapi import HTTPException, status
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.company import Company, UserCompany
from src.app.models.envelope_category import EnvelopeCategory
from src.app.schemas.company import CompanyResponse, UserCompanyResponse


class CompanyService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _get_cat_names(self) -> dict[str, str]:
        result = await self._session.execute(select(EnvelopeCategory.id, EnvelopeCategory.name))
        return dict(result.all())

    def _to_response(self, c: Company, cats: dict[str, str]) -> CompanyResponse:
        return CompanyResponse(
            id=c.id,
            name=c.name,
            abbr=c.abbr,
            color=c.color,
            category_id=c.category_id,
            category_name=cats.get(c.category_id) if c.category_id else None,
            description=c.description,
            promo_types=c.promo_types,
        )

    async def list_companies(
        self,
        search: str | None = None,
        category_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CompanyResponse], int]:
        query = select(Company).where(Company.is_active.is_(True))

        if search:
            query = query.where(Company.name.ilike(f"%{search}%"))
        if category_id:
            query = query.where(Company.category_id == category_id)

        count_q = query.with_only_columns(Company.id)
        count_result = await self._session.execute(count_q)
        total = len(count_result.all())

        query = query.order_by(Company.name).limit(limit).offset(offset)
        result = await self._session.execute(query)
        companies = result.scalars().all()
        cats = await self._get_cat_names()

        return [self._to_response(c, cats) for c in companies], total

    async def list_user_companies(self, user_id: uuid.UUID) -> list[UserCompanyResponse]:
        result = await self._session.execute(
            select(UserCompany).where(UserCompany.user_id == user_id).order_by(UserCompany.created_at.desc())
        )
        return [UserCompanyResponse.model_validate(uc) for uc in result.scalars().all()]

    async def add_user_company(self, user_id: uuid.UUID, company_id: str) -> UserCompanyResponse:
        company = await self._session.get(Company, company_id)
        if company is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

        existing = await self._session.execute(
            select(UserCompany).where(UserCompany.user_id == user_id, UserCompany.company_id == company_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Company already saved")

        uc = UserCompany(user_id=user_id, company_id=company_id)
        self._session.add(uc)
        await self._session.flush()
        await self._session.refresh(uc)
        await self._session.commit()
        return UserCompanyResponse.model_validate(uc)

    async def sync_user_companies(self, user_id: uuid.UUID, company_ids: list[str]) -> list[UserCompanyResponse]:
        await self._session.execute(sa_delete(UserCompany).where(UserCompany.user_id == user_id))

        existing_q = await self._session.execute(select(Company.id).where(Company.id.in_(company_ids)))
        valid_ids = {row[0] for row in existing_q.all()}

        result = []
        for cid in company_ids:
            if cid not in valid_ids:
                continue
            uc = UserCompany(user_id=user_id, company_id=cid)
            self._session.add(uc)
            await self._session.flush()
            await self._session.refresh(uc)
            result.append(UserCompanyResponse.model_validate(uc))
        await self._session.commit()
        return result

    async def remove_user_company(self, user_id: uuid.UUID, company_id: str) -> None:
        result = await self._session.execute(
            sa_delete(UserCompany).where(UserCompany.user_id == user_id, UserCompany.company_id == company_id)
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User company not found")
        await self._session.commit()
