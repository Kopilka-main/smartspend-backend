import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.repositories.notification import NotificationRepository
from src.app.schemas.notification import NotificationResponse


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = NotificationRepository(session)

    async def list_notifications(
        self, user_id: uuid.UUID, notif_type: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> tuple[list[NotificationResponse], int]:
        notifs, total = await self._repo.list_by_user(user_id, notif_type, limit, offset)
        return [
            NotificationResponse(
                id=n.id, user_id=str(n.user_id), type=n.type,
                title=n.title, description=n.description,
                is_read=n.is_read, payload=n.payload,
                created_at=n.created_at,
            )
            for n in notifs
        ], total

    async def count_unread(self, user_id: uuid.UUID) -> int:
        return await self._repo.count_unread(user_id)

    async def mark_read(self, notification_id: int, user_id: uuid.UUID) -> None:
        await self._repo.mark_read(notification_id, user_id)
        await self._session.commit()

    async def mark_all_read(self, user_id: uuid.UUID) -> None:
        await self._repo.mark_all_read(user_id)
        await self._session.commit()
