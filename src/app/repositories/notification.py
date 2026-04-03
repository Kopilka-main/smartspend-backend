import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        notif_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        base = select(Notification).where(Notification.user_id == user_id)
        if notif_type and notif_type != "all":
            base = base.where(Notification.type == notif_type)

        count_q = select(func.count()).select_from(base.with_only_columns(Notification.id).subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        base = base.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(base)
        return list(result.scalars().all()), total

    async def count_unread(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count()).where(
            Notification.user_id == user_id, Notification.is_read.is_(False)
        )
        return (await self._session.execute(stmt)).scalar_one()

    async def create(self, notification: Notification) -> Notification:
        self._session.add(notification)
        await self._session.flush()
        await self._session.refresh(notification)
        return notification

    async def mark_read(self, notification_id: int, user_id: uuid.UUID) -> None:
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(is_read=True)
        )
        await self._session.execute(stmt)

    async def mark_all_read(self, user_id: uuid.UUID) -> None:
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        await self._session.execute(stmt)
