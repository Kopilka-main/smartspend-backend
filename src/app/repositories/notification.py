import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.notification import Notification
from src.app.models.notification_message import NotificationMessage


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
        base = select(Notification).where(Notification.user_id == user_id, Notification.is_deleted.is_(False))
        if notif_type and notif_type != "all":
            base = base.where(Notification.type == notif_type)

        count_q = select(func.count()).select_from(base.with_only_columns(Notification.id).subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        base = base.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(base)
        return list(result.scalars().all()), total

    async def get_by_id(self, notification_id: int) -> Notification | None:
        return await self._session.get(Notification, notification_id)

    async def count_unread(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count()).where(Notification.user_id == user_id, Notification.is_read.is_(False))
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

    async def set_action(self, notification_id: int, user_id: uuid.UUID, action_status: str) -> None:
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(action_status=action_status, is_read=True)
        )
        await self._session.execute(stmt)

    async def list_messages(self, notification_id: int) -> list[NotificationMessage]:
        stmt = (
            select(NotificationMessage)
            .where(NotificationMessage.notification_id == notification_id)
            .order_by(NotificationMessage.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_message(self, message: NotificationMessage) -> NotificationMessage:
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)
        return message

    async def increment_messages_count(self, notification_id: int) -> None:
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id)
            .values(messages_count=Notification.messages_count + 1)
        )
        await self._session.execute(stmt)

    async def soft_delete(self, notification_id: int, user_id: uuid.UUID) -> None:
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(is_deleted=True)
        )
        await self._session.execute(stmt)

    async def restore(self, notification_id: int, user_id: uuid.UUID) -> None:
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(is_deleted=False)
        )
        await self._session.execute(stmt)
