import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.article import Article
from src.app.models.follow import Follow
from src.app.models.set import Set
from src.app.schemas.feed import FeedItem
from src.app.schemas.user import AuthorInfo


def _author_info(user) -> AuthorInfo | None:
    if user is None:
        return None
    if getattr(user, "deleted_at", None) is not None:
        return AuthorInfo(
            id=user.id, display_name="👻 Привидение",
            initials="👻", color=user.color,
        )
    return AuthorInfo(
        id=user.id, display_name=user.display_name,
        initials=user.initials, color=user.color,
        avatar_url=user.avatar_url,
    )


class FeedService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_feed(
        self, user_id: uuid.UUID | None = None,
        feed_type: str = "all", mode: str | None = None,
        category_id: str | None = None, search: str | None = None,
        sort: str = "newest", limit: int = 20, offset: int = 0,
    ) -> tuple[list[FeedItem], int]:
        items: list[FeedItem] = []
        total = 0

        if feed_type in ("all", "articles"):
            a_items, a_total = await self._get_articles(
                user_id, mode, category_id, search, sort, limit, offset,
            )
            items.extend(a_items)
            total += a_total

        if feed_type in ("all", "sets"):
            s_items, s_total = await self._get_sets(
                category_id, search, sort, limit, offset,
            )
            items.extend(s_items)
            total += s_total

        if sort == "popular":
            items.sort(key=lambda x: (x.likes_count or 0) + (x.users_count or 0), reverse=True)
        else:
            items.sort(key=lambda x: x.created_at, reverse=True)

        return items[:limit], total

    async def _get_articles(
        self, user_id, mode, category_id, search, sort, limit, offset,
    ) -> tuple[list[FeedItem], int]:
        base = select(Article).options(
            selectinload(Article.author)
        ).where(Article.status == "published")

        if mode == "subscriptions" and user_id:
            following_ids = select(Follow.following_id).where(Follow.follower_id == user_id)
            base = base.where(Article.author_id.in_(following_ids))

        if category_id and category_id != "all":
            base = base.where(Article.category_id == category_id)
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            base = base.where(Article.title.ilike(pattern) | Article.preview.ilike(pattern))

        count_q = select(func.count()).select_from(base.with_only_columns(Article.id).subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        if sort == "popular":
            base = base.order_by(Article.likes_count.desc())
        else:
            base = base.order_by(Article.published_at.desc().nullslast())

        base = base.limit(limit).offset(offset)
        result = await self._session.execute(base)

        return [
            FeedItem(
                id=a.id, type="article", title=a.title, preview=a.preview,
                category_id=a.category_id, published_at=a.published_at,
                created_at=a.created_at, author=_author_info(a.author),
                views_count=a.views_count, likes_count=a.likes_count,
                dislikes_count=a.dislikes_count, article_type=a.article_type,
            )
            for a in result.scalars().unique().all()
        ], total

    async def _get_sets(
        self, category_id, search, sort, limit, offset,
    ) -> tuple[list[FeedItem], int]:
        base = select(Set).options(
            selectinload(Set.items), selectinload(Set.author)
        ).where(Set.is_private.is_(False), Set.hidden.is_(False))

        if category_id and category_id != "all":
            base = base.where(Set.category_id == category_id)
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            base = base.where(Set.title.ilike(pattern) | Set.description.ilike(pattern))

        count_q = select(func.count()).select_from(base.with_only_columns(Set.id).subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        if sort == "popular":
            base = base.order_by(Set.users_count.desc())
        else:
            base = base.order_by(Set.created_at.desc())

        base = base.limit(limit).offset(offset)
        result = await self._session.execute(base)

        return [
            FeedItem(
                id=s.id, type="set", title=s.title, preview=s.description,
                category_id=s.category_id, published_at=s.added,
                created_at=s.created_at, author=_author_info(s.author),
                items_count=len(s.items) if s.items else 0,
                amount=s.amount, users_count=s.users_count,
                source=s.source, color=s.color,
            )
            for s in result.scalars().unique().all()
        ], total
