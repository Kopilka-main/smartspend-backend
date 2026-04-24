import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.envelope import Envelope
from src.app.models.envelope_category import EnvelopeCategory
from src.app.models.set import Set


class EnvelopeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, envelope_id: int) -> Envelope | None:
        return await self._session.get(Envelope, envelope_id)

    async def list_by_user(self, user_id: uuid.UUID) -> list[tuple[Envelope, str | None]]:
        stmt = (
            select(Envelope, Set.source)
            .outerjoin(Set, Envelope.set_id == Set.id)
            .where(Envelope.user_id == user_id)
            .order_by(Envelope.category_id, Envelope.created_at)
        )
        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def find_by_user_set(self, user_id: uuid.UUID, set_id: str) -> Envelope | None:
        stmt = select(Envelope).where(Envelope.user_id == user_id, Envelope.set_id == set_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, envelope: Envelope) -> Envelope:
        self._session.add(envelope)
        await self._session.flush()
        await self._session.refresh(envelope)
        return envelope

    async def delete_envelope(self, envelope_id: int) -> None:
        envelope = await self._session.get(Envelope, envelope_id)
        if envelope:
            await self._session.delete(envelope)
            await self._session.flush()

    async def delete_by_user_set(self, user_id: uuid.UUID, set_id: str) -> None:
        stmt = delete(Envelope).where(Envelope.user_id == user_id, Envelope.set_id == set_id)
        await self._session.execute(stmt)

    async def sum_amount_by_user(self, user_id: uuid.UUID) -> int:
        stmt = select(func.coalesce(func.sum(Envelope.amount), 0)).where(Envelope.user_id == user_id)
        return (await self._session.execute(stmt)).scalar_one()

    async def list_categories(self) -> list[EnvelopeCategory]:
        stmt = select(EnvelopeCategory).order_by(EnvelopeCategory.id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
