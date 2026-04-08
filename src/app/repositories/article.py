import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.article import Article, ArticleBlock
from src.app.models.article_comment import ArticleComment
from src.app.models.article_set_link import ArticleSetLink


class ArticleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, article_id: str) -> Article | None:
        stmt = (
            select(Article)
            .options(
                selectinload(Article.blocks),
                selectinload(Article.author),
                selectinload(Article.comments),
            )
            .where(Article.id == article_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_published(
        self,
        category_id: str | None = None,
        author_id: uuid.UUID | None = None,
        search: str | None = None,
        sort: str = "newest",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Article], int]:
        base = (
            select(Article)
            .options(selectinload(Article.author), selectinload(Article.comments))
            .where(Article.status == "published")
        )

        if category_id and category_id != "all":
            base = base.where(Article.category_id == category_id)
        if author_id:
            base = base.where(Article.author_id == author_id)
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            base = base.where(Article.title.ilike(pattern) | Article.preview.ilike(pattern))

        count_q = select(func.count()).select_from(base.with_only_columns(Article.id).subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        if sort == "popular":
            base = base.order_by(Article.likes_count.desc())
        else:
            base = base.order_by(Article.published_at.desc().nullslast(), Article.created_at.desc())

        base = base.limit(limit).offset(offset)
        result = await self._session.execute(base)
        return list(result.scalars().unique().all()), total

    async def list_by_author(self, author_id: uuid.UUID, limit: int = 50, offset: int = 0) -> tuple[list[Article], int]:
        base = (
            select(Article)
            .options(selectinload(Article.author), selectinload(Article.comments))
            .where(Article.author_id == author_id)
        )

        count_q = select(func.count()).select_from(base.with_only_columns(Article.id).subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        base = base.order_by(Article.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(base)
        return list(result.scalars().unique().all()), total

    async def count_by_author(self, author_id: uuid.UUID) -> int:
        stmt = select(func.count()).where(Article.author_id == author_id, Article.status == "published")
        return (await self._session.execute(stmt)).scalar_one()

    async def create(self, article: Article) -> Article:
        self._session.add(article)
        await self._session.flush()
        await self._session.refresh(article)
        return article

    async def add_blocks(self, blocks: list[ArticleBlock]) -> None:
        self._session.add_all(blocks)
        await self._session.flush()

    async def delete_blocks_by_article(self, article_id: str) -> None:
        stmt = delete(ArticleBlock).where(ArticleBlock.article_id == article_id)
        await self._session.execute(stmt)

    async def delete_article(self, article_id: str) -> None:
        article = await self.get_by_id(article_id)
        if article:
            await self._session.delete(article)
            await self._session.flush()

    async def list_comments(
        self, article_id: str, sort: str = "new", limit: int = 50, offset: int = 0
    ) -> tuple[list[ArticleComment], int]:
        base = select(ArticleComment).where(ArticleComment.article_id == article_id)
        count_q = select(func.count()).select_from(base.with_only_columns(ArticleComment.id).subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        if sort == "popular":
            base = base.order_by(ArticleComment.likes_count.desc())
        else:
            base = base.order_by(ArticleComment.created_at.desc())

        base = base.limit(limit).offset(offset)
        result = await self._session.execute(base)
        return list(result.scalars().all()), total

    async def add_comment(self, comment: ArticleComment) -> ArticleComment:
        self._session.add(comment)
        await self._session.flush()
        await self._session.refresh(comment)
        return comment

    async def get_comment(self, comment_id: int) -> ArticleComment | None:
        return await self._session.get(ArticleComment, comment_id)

    async def delete_comment(self, comment_id: int) -> None:
        comment = await self._session.get(ArticleComment, comment_id)
        if comment:
            await self._session.delete(comment)
            await self._session.flush()

    async def link_to_set(self, link: ArticleSetLink) -> ArticleSetLink:
        self._session.add(link)
        await self._session.flush()
        await self._session.refresh(link)
        return link

    async def unlink_from_set(self, article_id: str, user_id: uuid.UUID) -> None:
        stmt = delete(ArticleSetLink).where(
            ArticleSetLink.article_id == article_id,
            ArticleSetLink.user_id == user_id,
        )
        await self._session.execute(stmt)
