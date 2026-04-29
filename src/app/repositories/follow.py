import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.follow import Follow


class FollowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> bool:
        stmt = select(func.count()).where(Follow.follower_id == follower_id, Follow.following_id == following_id)
        return (await self._session.execute(stmt)).scalar_one() > 0

    async def create(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> Follow:
        follow = Follow(follower_id=follower_id, following_id=following_id)
        self._session.add(follow)
        await self._session.flush()
        return follow

    async def remove(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> None:
        stmt = delete(Follow).where(Follow.follower_id == follower_id, Follow.following_id == following_id)
        await self._session.execute(stmt)

    async def count_followers(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count()).where(Follow.following_id == user_id)
        return (await self._session.execute(stmt)).scalar_one()

    async def count_following(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count()).where(Follow.follower_id == user_id)
        return (await self._session.execute(stmt)).scalar_one()

    async def list_following(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        stmt = select(Follow.following_id).where(Follow.follower_id == user_id).order_by(Follow.created_at.desc())
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all()]

    async def list_followers(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        stmt = select(Follow.follower_id).where(Follow.following_id == user_id).order_by(Follow.created_at.desc())
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all()]
