import uuid

from fastapi import HTTPException, status
from sqlalchemy import delete as sa_delete
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.card import Card, UserCard
from src.app.models.company import Company, UserCompany
from src.app.schemas.card import (
    CardCalculateResponse,
    CardResponse,
    UserCardCreate,
    UserCardResponse,
)


class CardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _calc_cashback(card: Card, spending: dict | None) -> int | None:
        if not spending or not card.cashback:
            return None
        total = 0
        for cat, amount in spending.items():
            rate = card.cashback.get(cat, 0)
            total += int(float(amount) * float(rate) / 100)
        return total

    def _to_response(self, card: Card, spending: dict | None = None) -> CardResponse:
        return CardResponse(
            id=card.id,
            bank_name=card.bank_name,
            bank_color=card.bank_color,
            bank_text_color=card.bank_text_color,
            name=card.name,
            card_type=card.card_type,
            cashback=card.cashback,
            cashback_note=card.cashback_note,
            grace_days=card.grace_days,
            fee=card.fee,
            fee_base=card.fee_base,
            is_systemic=card.is_systemic,
            conditions=card.conditions,
            tags=card.tags,
            bonus_type=card.bonus_type,
            bonus_system=card.bonus_system,
            bonus_desc=card.bonus_desc,
            fee_desc=card.fee_desc,
            url=card.url,
            is_active=card.is_active,
            calc_cashback=self._calc_cashback(card, spending),
        )

    async def list_cards(
        self,
        card_type: str | None = None,
        bank_name: str | None = None,
        search: str | None = None,
        condition: str | None = None,
        scope: str = "all",
        sort: str = "cashback",
        spending: dict | None = None,
        user_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CardResponse], int]:
        query = select(Card).where(Card.is_active.is_(True))

        if card_type:
            query = query.where(Card.card_type == card_type)
        if bank_name:
            query = query.where(Card.bank_name == bank_name)
        if search:
            pattern = f"%{search}%"
            query = query.where(Card.bank_name.ilike(pattern) | Card.name.ilike(pattern))
        if condition and condition != "all":
            query = query.where(Card.conditions.any(condition))
        if scope == "mine" and user_id:
            sub = select(UserCompany.company_id).where(UserCompany.user_id == user_id)
            bank_sub = select(Company.name).where(Company.id.in_(sub))
            query = query.where(Card.bank_name.in_(bank_sub))

        count_q = query.with_only_columns(sa_func.count(Card.id))
        total = (await self._session.execute(count_q)).scalar() or 0

        result = await self._session.execute(query.limit(limit).offset(offset))
        cards = list(result.scalars().all())

        items = [self._to_response(c, spending) for c in cards]

        if sort == "cashback" and spending:
            items.sort(key=lambda x: x.calc_cashback or 0, reverse=True)
        elif sort == "grace":
            items.sort(key=lambda x: x.grace_days, reverse=True)
        elif sort == "cashback_grace" and spending:
            items.sort(key=lambda x: (x.calc_cashback or 0) * 100 + x.grace_days, reverse=True)
        else:
            items.sort(key=lambda x: x.bank_name)

        return items, total

    async def get_card(self, card_id: str) -> CardResponse:
        card = await self._session.get(Card, card_id)
        if card is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
        return self._to_response(card)

    async def calculate(self, spending: dict) -> list[CardCalculateResponse]:
        result = await self._session.execute(select(Card).where(Card.is_active.is_(True), Card.cashback.isnot(None)))
        cards = result.scalars().all()

        responses: list[CardCalculateResponse] = []
        for card in cards:
            cashback = card.cashback or {}
            breakdown: dict[str, int] = {}
            total = 0
            for category, amount in spending.items():
                rate = cashback.get(category, 0)
                cb = int(float(amount) * float(rate) / 100)
                if cb > 0:
                    breakdown[category] = cb
                    total += cb
            responses.append(
                CardCalculateResponse(
                    card_id=card.id,
                    card_name=card.name,
                    bank_name=card.bank_name,
                    total_cashback=total,
                    breakdown=breakdown,
                )
            )

        responses.sort(key=lambda r: r.total_cashback, reverse=True)
        return responses

    async def get_spending(self, user_id: uuid.UUID) -> dict:
        result = await self._session.execute(
            select(UserCard.spending).where(UserCard.user_id == user_id).order_by(UserCard.created_at.desc()).limit(1)
        )
        row = result.scalar_one_or_none()
        return row or {}

    async def update_spending(self, user_id: uuid.UUID, spending: dict) -> dict:
        result = await self._session.execute(select(UserCard.id).where(UserCard.user_id == user_id).limit(1))
        uc_id = result.scalar_one_or_none()
        if uc_id:
            await self._session.execute(sa_update(UserCard).where(UserCard.id == uc_id).values(spending=spending))
        else:
            uc = UserCard(user_id=user_id, card_id="__spending__", spending=spending)
            self._session.add(uc)
            await self._session.flush()
        await self._session.commit()
        return spending

    async def list_user_cards(self, user_id: uuid.UUID) -> list[UserCardResponse]:
        result = await self._session.execute(
            select(UserCard).where(UserCard.user_id == user_id).order_by(UserCard.created_at.desc())
        )
        return [UserCardResponse.model_validate(uc) for uc in result.scalars().all()]

    async def add_user_card(self, user_id: uuid.UUID, data: UserCardCreate) -> UserCardResponse:
        card = await self._session.get(Card, data.card_id)
        if card is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")

        existing = await self._session.execute(
            select(UserCard).where(UserCard.user_id == user_id, UserCard.card_id == data.card_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Card already saved")

        uc = UserCard(user_id=user_id, card_id=data.card_id, spending=data.spending)
        self._session.add(uc)
        await self._session.flush()
        await self._session.refresh(uc)
        await self._session.commit()
        return UserCardResponse.model_validate(uc)

    async def remove_user_card(self, user_card_id: int, user_id: uuid.UUID) -> None:
        uc = await self._session.get(UserCard, user_card_id)
        if uc is None or uc.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User card not found")
        await self._session.execute(sa_delete(UserCard).where(UserCard.id == user_card_id))
        await self._session.commit()
