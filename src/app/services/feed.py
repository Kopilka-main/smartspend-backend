import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.article import Article
from src.app.models.envelope import Envelope
from src.app.models.envelope_category import EnvelopeCategory
from src.app.models.follow import Follow
from src.app.models.reaction import Reaction
from src.app.models.set import Set
from src.app.schemas.feed import FeedItem, SetLinkInfo
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


class FeedService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_feed(
        self,
        user_id: uuid.UUID | None = None,
        mode: str | None = None,
        category_ids: list[str] | None = None,
        search: str | None = None,
        sort: str = "popular_7d",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[FeedItem], int]:
        base = (
            select(Article)
            .options(selectinload(Article.author), selectinload(Article.comments))
            .where(Article.status == "published")
        )

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
            base = base.where(
                (Article.linked_set_id.in_(user_set_ids))
                | (
                    Article.linked_set_ids.overlap(
                        select(Envelope.set_id).where(Envelope.user_id == user_id).scalar_subquery()
                    )
                )
            )

        if category_ids:
            filtered = [c for c in category_ids if c and c != "all"]
            if filtered:
                base = base.where(Article.category_id.in_(filtered))

        if search and search.strip():
            q = search.strip()
            if q.startswith("#"):
                tag = q.lstrip("#")
                base = base.where(Article.tags.any(tag))
            else:
                pattern = f"%{q}%"
                base = base.where(Article.title.ilike(pattern) | Article.preview.ilike(pattern) | Article.tags.any(q))

        if sort.startswith("popular"):
            count_q = select(func.count()).select_from(base.with_only_columns(Article.id).subquery())
            total = (await self._session.execute(count_q)).scalar_one()
            base = base.order_by(Article.likes_count.desc())
        else:
            count_q = select(func.count()).select_from(base.with_only_columns(Article.id).subquery())
            total = (await self._session.execute(count_q)).scalar_one()
            base = base.order_by(Article.published_at.desc().nullslast())

        base = base.limit(limit).offset(offset)
        result = await self._session.execute(base)
        articles = list(result.scalars().unique().all())

        set_ids = set()
        cat_ids = set()
        for a in articles:
            if a.linked_set_id:
                set_ids.add(a.linked_set_id)
            if a.category_id:
                cat_ids.add(a.category_id)

        sets_map: dict[str, tuple[str, str]] = {}
        if set_ids:
            st = await self._session.execute(select(Set.id, Set.title, Set.color).where(Set.id.in_(set_ids)))
            for row in st.all():
                sets_map[row[0]] = (row[1], row[2])

        cats_map: dict[str, str] = {}
        if cat_ids:
            ct = await self._session.execute(
                select(EnvelopeCategory.id, EnvelopeCategory.name).where(EnvelopeCategory.id.in_(cat_ids))
            )
            cats_map = dict(ct.all())

        items = []
        for a in articles:
            set_link = None
            if a.linked_set_id and a.linked_set_id in sets_map:
                t, c = sets_map[a.linked_set_id]
                set_link = SetLinkInfo(title=t, color=c)

            items.append(
                FeedItem(
                    id=a.id,
                    title=a.title,
                    preview=a.preview,
                    category_id=a.category_id,
                    category_name=cats_map.get(a.category_id),
                    published_at=a.published_at,
                    created_at=a.created_at,
                    author=_author_info(a.author),
                    tags=a.tags,
                    views_count=a.views_count,
                    likes_count=a.likes_count,
                    dislikes_count=a.dislikes_count,
                    comments_count=len(a.comments) if a.comments else 0,
                    article_type=a.article_type,
                    linked_set_id=a.linked_set_id,
                    linked_set_title=sets_map[a.linked_set_id][0]
                    if a.linked_set_id and a.linked_set_id in sets_map
                    else None,
                    set_link=set_link,
                )
            )
        return items, total

    async def get_tags(self) -> list[str]:
        stmt = select(Article.tags).where(Article.status == "published", Article.tags.isnot(None))
        result = await self._session.execute(stmt)
        all_tags: set[str] = set()
        for row in result.scalars().all():
            if row:
                all_tags.update(row)
        return sorted(all_tags)
