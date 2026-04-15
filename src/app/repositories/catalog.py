from datetime import date, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.set import Set, SetItem
from src.app.models.set_comment import SetComment


class CatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, set_id: str) -> Set | None:
        stmt = (
            select(Set)
            .options(
                selectinload(Set.items), selectinload(Set.author), selectinload(Set.comments), selectinload(Set.photos)
            )
            .where(Set.id == set_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_public(
        self,
        category_id: str | None = None,
        source: str | None = None,
        set_type: str | None = None,
        search: str | None = None,
        sort: str = "newest",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Set], int]:
        base = (
            select(Set)
            .options(selectinload(Set.items), selectinload(Set.author), selectinload(Set.comments))
            .where(Set.is_private.is_(False), Set.hidden.is_(False))
        )

        if category_id and category_id != "all":
            base = base.where(Set.category_id == category_id)
        if source and source != "all":
            base = base.where(Set.source == source)
        if set_type and set_type != "all":
            base = base.where(Set.set_type == set_type)
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            base = base.where(Set.title.ilike(pattern) | Set.description.ilike(pattern))

        if sort.startswith("popular"):
            if sort == "popular_7d":
                week_ago = date.today() - timedelta(days=7)
                base = base.where(Set.created_at >= week_ago)
            elif sort == "popular_30d":
                month_ago = date.today() - timedelta(days=30)
                base = base.where(Set.created_at >= month_ago)
            count_q = select(func.count()).select_from(base.with_only_columns(Set.id).subquery())
            total = (await self._session.execute(count_q)).scalar_one()
            base = base.order_by(Set.users_count.desc())
        else:
            count_q = select(func.count()).select_from(base.with_only_columns(Set.id).subquery())
            total = (await self._session.execute(count_q)).scalar_one()
            base = base.order_by(Set.created_at.desc())

        base = base.limit(limit).offset(offset)
        result = await self._session.execute(base)
        return list(result.scalars().unique().all()), total

    async def list_by_author(self, author_id, limit: int = 50, offset: int = 0) -> tuple[list[Set], int]:
        base = (
            select(Set)
            .options(selectinload(Set.items), selectinload(Set.author), selectinload(Set.comments))
            .where(Set.author_id == author_id, Set.hidden.is_(False))
        )

        count_q = select(func.count()).select_from(base.with_only_columns(Set.id).subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        base = base.order_by(Set.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(base)
        return list(result.scalars().unique().all()), total

    async def create(self, s: Set) -> Set:
        self._session.add(s)
        await self._session.flush()
        await self._session.refresh(s)
        return s

    async def add_items(self, items: list[SetItem]) -> None:
        self._session.add_all(items)
        await self._session.flush()

    async def delete_items_by_set(self, set_id: str) -> None:
        stmt = delete(SetItem).where(SetItem.set_id == set_id)
        await self._session.execute(stmt)

    async def delete_set(self, set_id: str) -> None:
        s = await self.get_by_id(set_id)
        if s:
            await self._session.delete(s)
            await self._session.flush()

    async def list_comments(
        self, set_id: str, sort: str = "new", limit: int = 50, offset: int = 0
    ) -> tuple[list[SetComment], int]:
        base = select(SetComment).where(SetComment.set_id == set_id)
        count_q = select(func.count()).select_from(base.with_only_columns(SetComment.id).subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        if sort == "popular":
            base = base.order_by(SetComment.likes_count.desc())
        else:
            base = base.order_by(SetComment.created_at.desc())

        base = base.limit(limit).offset(offset)
        result = await self._session.execute(base)
        return list(result.scalars().all()), total

    async def add_comment(self, comment: SetComment) -> SetComment:
        self._session.add(comment)
        await self._session.flush()
        await self._session.refresh(comment)
        return comment

    async def get_comment(self, comment_id: int) -> SetComment | None:
        return await self._session.get(SetComment, comment_id)

    async def delete_comment(self, comment_id: int) -> None:
        comment = await self._session.get(SetComment, comment_id)
        if comment:
            await self._session.delete(comment)
            await self._session.flush()
