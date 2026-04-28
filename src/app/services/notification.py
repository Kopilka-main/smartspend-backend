import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.notification_message import NotificationMessage
from src.app.models.user import User
from src.app.repositories.notification import NotificationRepository
from src.app.schemas.notification import (
    NotificationMessageResponse,
    NotificationResponse,
)
from src.app.schemas.user import AuthorInfo


def _build_author(user: User) -> AuthorInfo:
    return AuthorInfo(
        id=user.id,
        display_name=user.display_name,
        username=user.username,
        initials=user.initials,
        color=user.color,
        avatar_url=user.avatar_url,
    )


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = NotificationRepository(session)

    async def _resolve_authors(self, author_ids: set[uuid.UUID]) -> dict[uuid.UUID, AuthorInfo]:
        if not author_ids:
            return {}
        stmt = select(User).where(User.id.in_(author_ids))
        result = await self._session.execute(stmt)
        return {u.id: _build_author(u) for u in result.scalars().all()}

    async def list_notifications(
        self,
        user_id: uuid.UUID,
        notif_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[NotificationResponse], int]:
        notifs, total = await self._repo.list_by_user(user_id, notif_type, limit, offset)

        author_ids = {n.author_id for n in notifs if n.author_id}
        authors = await self._resolve_authors(author_ids)

        return [
            NotificationResponse(
                id=n.id,
                user_id=str(n.user_id),
                type=n.type,
                title=n.title,
                description=n.description,
                is_read=n.is_read,
                payload=n.payload,
                action_status=n.action_status,
                author_id=str(n.author_id) if n.author_id else None,
                author=authors.get(n.author_id) if n.author_id else None,
                direction=n.direction,
                set_id=n.set_id,
                set_title=n.set_title,
                article_id=n.article_id,
                article_title=n.article_title,
                messages_count=n.messages_count,
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

    async def set_action(self, notification_id: int, user_id: uuid.UUID, action_status: str) -> None:
        await self._repo.set_action(notification_id, user_id, action_status)
        await self._session.commit()

    async def add_message(self, notification_id: int, user_id: uuid.UUID, text: str) -> NotificationMessageResponse:
        notif = await self._repo.get_by_id(notification_id)
        if notif is None or notif.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

        msg = NotificationMessage(notification_id=notification_id, user_id=user_id, text=text)
        msg = await self._repo.add_message(msg)
        await self._repo.increment_messages_count(notification_id)
        await self._session.commit()

        authors = await self._resolve_authors({user_id})
        return NotificationMessageResponse(
            id=msg.id,
            notification_id=msg.notification_id,
            user_id=str(msg.user_id) if msg.user_id else None,
            author=authors.get(user_id),
            text=msg.text,
            created_at=msg.created_at,
        )

    async def list_messages(self, notification_id: int, user_id: uuid.UUID) -> list[NotificationMessageResponse]:
        notif = await self._repo.get_by_id(notification_id)
        if notif is None or notif.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

        messages = await self._repo.list_messages(notification_id)
        author_ids = {m.user_id for m in messages if m.user_id}
        authors = await self._resolve_authors(author_ids)

        return [
            NotificationMessageResponse(
                id=m.id,
                notification_id=m.notification_id,
                user_id=str(m.user_id) if m.user_id else None,
                author=authors.get(m.user_id) if m.user_id else None,
                text=m.text,
                created_at=m.created_at,
            )
            for m in messages
        ]

    async def withdraw(self, notification_id: int, user_id: uuid.UUID) -> None:
        notif = await self._repo.get_by_id(notification_id)
        if notif is None or notif.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        if notif.type != "request":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only requests can be withdrawn")
        await self._repo.set_action(notification_id, user_id, "withdrawn")
        await self._session.commit()
