import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.notification import Notification
from src.app.models.user import User
from src.app.repositories.follow import FollowRepository
from src.app.repositories.notification import NotificationRepository
from src.app.repositories.user import UserRepository


class FollowService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = FollowRepository(session)

    async def follow(self, follower: User, following_id: uuid.UUID) -> None:
        if follower.id == following_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot follow yourself",
            )

        user_repo = UserRepository(self._session)
        target = await user_repo.get_by_id(following_id)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        already = await self._repo.exists(follower.id, following_id)
        if already:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already following")

        await self._repo.create(follower.id, following_id)

        notif_repo = NotificationRepository(self._session)
        await notif_repo.create(
            Notification(
                user_id=following_id,
                type="activity",
                title="Новый подписчик",
                description=f"На вас подписался {follower.display_name}",
                payload=f"/author/{follower.id}",
            )
        )

        await self._session.commit()

    async def unfollow(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> None:
        exists = await self._repo.exists(follower_id, following_id)
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not following this user",
            )
        await self._repo.remove(follower_id, following_id)
        await self._session.commit()
