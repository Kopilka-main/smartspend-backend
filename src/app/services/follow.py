import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.article import Article
from src.app.models.follow import Follow
from src.app.models.notification import Notification
from src.app.models.set import Set
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

    async def _counts_for(self, user_id: uuid.UUID) -> tuple[int, int, int]:
        followers = await self._session.execute(
            select(func.count()).select_from(Follow).where(Follow.following_id == user_id)
        )
        articles = await self._session.execute(
            select(func.count()).select_from(Article).where(Article.author_id == user_id, Article.status == "published")
        )
        sets = await self._session.execute(
            select(func.count())
            .select_from(Set)
            .where(Set.author_id == user_id, Set.hidden.is_(False), Set.is_private.is_(False))
        )
        return (
            followers.scalar_one() or 0,
            articles.scalar_one() or 0,
            sets.scalar_one() or 0,
        )

    async def list_following(self, user_id: uuid.UUID) -> list:
        from src.app.schemas.user import AuthorInfo

        ids = await self._repo.list_following(user_id)
        if not ids:
            return []
        user_repo = UserRepository(self._session)
        result = []
        for uid in ids:
            u = await user_repo.get_by_id(uid)
            if u:
                fc, ac, sc = await self._counts_for(uid)
                result.append(
                    AuthorInfo(
                        id=u.id,
                        display_name=u.display_name,
                        username=u.username,
                        initials=u.initials,
                        color=u.color,
                        bio=u.bio,
                        avatar_url=u.avatar_url,
                        followers_count=fc,
                        articles_count=ac,
                        sets_count=sc,
                    )
                )
        return result

    async def list_followers(self, user_id: uuid.UUID) -> list:
        from src.app.schemas.user import AuthorInfo

        ids = await self._repo.list_followers(user_id)
        if not ids:
            return []
        user_repo = UserRepository(self._session)
        result = []
        for uid in ids:
            u = await user_repo.get_by_id(uid)
            if u:
                fc, ac, sc = await self._counts_for(uid)
                result.append(
                    AuthorInfo(
                        id=u.id,
                        display_name=u.display_name,
                        username=u.username,
                        initials=u.initials,
                        color=u.color,
                        bio=u.bio,
                        avatar_url=u.avatar_url,
                        followers_count=fc,
                        articles_count=ac,
                        sets_count=sc,
                    )
                )
        return result
