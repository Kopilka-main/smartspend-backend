import uuid

from fastapi import HTTPException, status
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.card import Card, UserCard
from src.app.schemas.card import (
    CardCalculateResponse,
    CardResponse,
    UserCardCreate,
    UserCardResponse,
)


class CardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_cards(
        self,
        card_type: str | None = None,
        bank_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CardResponse], int]:
        query = select(Card).where(Card.is_active.is_(True))

        if card_type:
            query = query.where(Card.card_type == card_type)
        if bank_name:
            query = query.where(Card.bank_name.ilike(f"%{bank_name}%"))

        count_q = query.with_only_columns(Card.id)
        count_result = await self._session.execute(count_q)
        total = len(count_result.all())

        query = query.order_by(Card.bank_name, Card.name).limit(limit).offset(offset)
        result = await self._session.execute(query)
        cards = result.scalars().all()

        return [CardResponse.model_validate(c) for c in cards], total

    async def get_card(self, card_id: str) -> CardResponse:
        card = await self._session.get(Card, card_id)
        if card is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
        return CardResponse.model_validate(card)

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
