import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.article import Article
from src.app.models.article_read import ArticleRead
from src.app.models.envelope import Envelope
from src.app.models.follow import Follow
from src.app.models.reaction import Reaction
from src.app.models.set import Set
from src.app.schemas.feed import FeedItem
from src.app.schemas.user import AuthorInfo


def _author_info(user) -> AuthorInfo | None:
    if user is None:
        return None
    if getattr(user, "deleted_at", None) is not None:
        return AuthorInfo(
            id=user.id,
            display_name="👻 Привидение",
            initials="👻",
            color=user.color,
        )
    return AuthorInfo(
        id=user.id,
        display_name=user.display_name,
        initials=user.initials,
        color=user.color,
        avatar_url=user.avatar_url,
    )


def _apply_popular_period(base, sort_val: str, date_col):
    if sort_val == "popular_7d":
        return base.where(date_col >= date.today() - timedelta(days=7))
    if sort_val == "popular_30d":
        return base.where(date_col >= date.today() - timedelta(days=30))
    return base


class FeedService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_feed(
        self,
        user_id: uuid.UUID | None = None,
        feed_type: str = "all",
        mode: str | None = None,
        category_id: str | None = None,
        search: str | None = None,
        sort: str = "newest",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[FeedItem], int]:
        items: list[FeedItem] = []
        total = 0

        fetch_limit = limit + offset if feed_type == "all" else limit
        fetch_offset = 0 if feed_type == "all" else offset

        include_articles = feed_type in ("all", "articles")
        include_sets = feed_type in ("all", "sets")
        include_coupons = feed_type in ("all", "coupons")

        if include_articles or include_coupons:
            a_items, a_total = await self._get_articles(
                user_id,
                mode,
                category_id,
                search,
                sort,
                fetch_limit,
                fetch_offset,
                article_type="coupon" if feed_type == "coupons" else None,
            )
            items.extend(a_items)
            total += a_total

        if include_sets and feed_type != "coupons":
            s_items, s_total = await self._get_sets(
                user_id,
                mode,
                category_id,
                search,
                sort,
                fetch_limit,
                fetch_offset,
            )
            items.extend(s_items)
            total += s_total

        if sort.startswith("popular"):
            items.sort(key=lambda x: (x.likes_count or 0) + (x.users_count or 0), reverse=True)
        else:
            items.sort(key=lambda x: x.created_at, reverse=True)

        if feed_type == "all":
            return items[offset : offset + limit], total
        return items[:limit], total

    async def _get_articles(
        self,
        user_id,
        mode,
        category_id,
        search,
        sort,
        limit,
        offset,
        article_type: str | None = None,
    ) -> tuple[list[FeedItem], int]:
        base = (
            select(Article)
            .options(selectinload(Article.author), selectinload(Article.comments))
            .where(Article.status == "published")
        )

        if article_type:
            base = base.where(Article.article_type == article_type)

        if mode == "subscriptions" and user_id:
            following_ids = select(Follow.following_id).where(Follow.follower_id == user_id)
            base = base.where(Article.author_id.in_(following_ids))
        elif mode == "liked" and user_id:
            liked_ids = select(Reaction.target_id).where(
                Reaction.user_id == user_id, Reaction.target_type == "article", Reaction.type == "like"
            )
            base = base.where(Article.id.in_(liked_ids))
        elif mode == "my_sets" and user_id:
            user_set_ids = select(Envelope.set_id).where(Envelope.user_id == user_id)
            base = base.where(Article.linked_set_id.in_(user_set_ids))
        elif mode == "unread" and user_id:
            read_ids = select(ArticleRead.article_id).where(ArticleRead.user_id == user_id)
            base = base.where(Article.id.notin_(read_ids))

        if category_id and category_id != "all":
            base = base.where(Article.category_id == category_id)
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            base = base.where(Article.title.ilike(pattern) | Article.preview.ilike(pattern))

        if sort.startswith("popular"):
            base = _apply_popular_period(base, sort, Article.published_at)

        count_q = select(func.count()).select_from(base.with_only_columns(Article.id).subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        if sort.startswith("popular"):
            base = base.order_by(Article.likes_count.desc())
        else:
            base = base.order_by(Article.published_at.desc().nullslast())

        base = base.limit(limit).offset(offset)
        result = await self._session.execute(base)
        articles = list(result.scalars().unique().all())

        set_ids = {a.linked_set_id for a in articles if a.linked_set_id}
        set_titles: dict[str, str] = {}
        if set_ids:
            st = await self._session.execute(select(Set.id, Set.title).where(Set.id.in_(set_ids)))
            set_titles = dict(st.all())

        return [
            FeedItem(
                id=a.id,
                type="article",
                title=a.title,
                preview=a.preview,
                category_id=a.category_id,
                published_at=a.published_at,
                created_at=a.created_at,
                author=_author_info(a.author),
                views_count=a.views_count,
                likes_count=a.likes_count,
                dislikes_count=a.dislikes_count,
                comments_count=len(a.comments) if a.comments else 0,
                article_type=a.article_type,
                linked_set_id=a.linked_set_id,
                linked_set_title=set_titles.get(a.linked_set_id) if a.linked_set_id else None,
            )
            for a in articles
        ], total

    async def _get_sets(
        self,
        user_id,
        mode,
        category_id,
        search,
        sort,
        limit,
        offset,
    ) -> tuple[list[FeedItem], int]:
        base = (
            select(Set)
            .options(selectinload(Set.items), selectinload(Set.author))
            .where(Set.is_private.is_(False), Set.hidden.is_(False))
        )

        if mode == "subscriptions" and user_id:
            following_ids = select(Follow.following_id).where(Follow.follower_id == user_id)
            base = base.where(Set.author_id.in_(following_ids))
        elif mode == "liked" and user_id:
            liked_ids = select(Reaction.target_id).where(
                Reaction.user_id == user_id, Reaction.target_type == "set", Reaction.type == "like"
            )
            base = base.where(Set.id.in_(liked_ids))
        elif mode == "my_sets" and user_id:
            user_set_ids = select(Envelope.set_id).where(Envelope.user_id == user_id)
            base = base.where(Set.id.in_(user_set_ids))

        if category_id and category_id != "all":
            base = base.where(Set.category_id == category_id)
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            base = base.where(Set.title.ilike(pattern) | Set.description.ilike(pattern))

        if sort.startswith("popular"):
            base = _apply_popular_period(base, sort, Set.created_at)

        count_q = select(func.count()).select_from(base.with_only_columns(Set.id).subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        if sort.startswith("popular"):
            base = base.order_by(Set.users_count.desc())
        else:
            base = base.order_by(Set.created_at.desc())

        base = base.limit(limit).offset(offset)
        result = await self._session.execute(base)

        return [
            FeedItem(
                id=s.id,
                type="set",
                title=s.title,
                preview=s.description,
                category_id=s.category_id,
                published_at=s.added,
                created_at=s.created_at,
                author=_author_info(s.author),
                items_count=len(s.items) if s.items else 0,
                amount=s.amount,
                users_count=s.users_count,
                source=s.source,
                color=s.color,
            )
            for s in result.scalars().unique().all()
        ], total
