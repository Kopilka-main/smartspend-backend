import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.reaction import Reaction


class ReactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find(
        self, user_id: uuid.UUID, target_type: str, target_id: str
    ) -> Reaction | None:
        stmt = select(Reaction).where(
            Reaction.user_id == user_id,
            Reaction.target_type == target_type,
            Reaction.target_id == target_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self, user_id: uuid.UUID, target_type: str, target_id: str, reaction_type: str
    ) -> Reaction:
        existing = await self.find(user_id, target_type, target_id)
        if existing:
            existing.type = reaction_type
            await self._session.flush()
            return existing
        reaction = Reaction(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            type=reaction_type,
        )
        self._session.add(reaction)
        await self._session.flush()
        await self._session.refresh(reaction)
        return reaction

    async def remove(self, user_id: uuid.UUID, target_type: str, target_id: str) -> None:
        stmt = delete(Reaction).where(
            Reaction.user_id == user_id,
            Reaction.target_type == target_type,
            Reaction.target_id == target_id,
        )
        await self._session.execute(stmt)

    async def count(self, target_type: str, target_id: str, reaction_type: str) -> int:
        stmt = select(func.count()).where(
            Reaction.target_type == target_type,
            Reaction.target_id == target_id,
            Reaction.type == reaction_type,
        )
        return (await self._session.execute(stmt)).scalar_one()

    async def list_by_user(
        self, user_id: uuid.UUID, target_type: str | None = None
    ) -> list[Reaction]:
        stmt = select(Reaction).where(Reaction.user_id == user_id)
        if target_type and target_type != "all":
            stmt = stmt.where(Reaction.target_type == target_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
