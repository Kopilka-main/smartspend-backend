import time
import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.article import Article, ArticleBlock
from src.app.models.article_comment import ArticleComment
from src.app.models.article_set_link import ArticleSetLink
from src.app.models.user import User
from src.app.repositories.article import ArticleRepository
from src.app.schemas.article import (
    ArticleCommentCreate,
    ArticleCommentResponse,
    ArticleCreate,
    ArticleListItem,
    ArticleResponse,
    ArticleSetLinkCreate,
    ArticleUpdate,
)
from src.app.schemas.user import AuthorInfo


def _author_info(user) -> AuthorInfo | None:
    if user is None:
        return None
    if user.deleted_at is not None:
        return AuthorInfo(
            id=user.id, display_name="👻 Привидение",
            initials="👻", color=user.color,
        )
    return AuthorInfo(
        id=user.id, display_name=user.display_name,
        initials=user.initials, color=user.color,
        avatar_url=user.avatar_url,
    )


def _article_to_response(a: Article) -> ArticleResponse:
    return ArticleResponse(
        id=a.id, title=a.title, article_type=a.article_type,
        category_id=a.category_id, preview=a.preview,
        published_at=a.published_at, status=a.status,
        views_count=a.views_count, likes_count=a.likes_count,
        dislikes_count=a.dislikes_count, linked_set_id=a.linked_set_id,
        blocks=[],
        author=_author_info(a.author),
        created_at=a.created_at, updated_at=a.updated_at,
    )


def _article_to_list_item(a: Article) -> ArticleListItem:
    return ArticleListItem(
        id=a.id, title=a.title, article_type=a.article_type,
        category_id=a.category_id, preview=a.preview,
        published_at=a.published_at, status=a.status,
        views_count=a.views_count, likes_count=a.likes_count,
        dislikes_count=a.dislikes_count, linked_set_id=a.linked_set_id,
        author=_author_info(a.author),
        created_at=a.created_at,
    )


class ArticleService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ArticleRepository(session)

    async def list_published(
        self, category_id: str | None = None, author_id: uuid.UUID | None = None,
        search: str | None = None, sort: str = "newest",
        limit: int = 20, offset: int = 0,
    ) -> tuple[list[ArticleListItem], int]:
        articles, total = await self._repo.list_published(
            category_id=category_id, author_id=author_id,
            search=search, sort=sort, limit=limit, offset=offset,
        )
        return [_article_to_list_item(a) for a in articles], total

    async def list_by_author(
        self, author_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> tuple[list[ArticleListItem], int]:
        articles, total = await self._repo.list_by_author(author_id, limit, offset)
        return [_article_to_list_item(a) for a in articles], total

    async def get_article(self, article_id: str) -> ArticleResponse:
        a = await self._repo.get_by_id(article_id)
        if a is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
        resp = _article_to_response(a)
        resp.blocks = [
            {"id": b.id, "position": b.position, "type": b.type,
             "text": b.text, "html": b.html, "items": b.items, "title": b.title}
            for b in (a.blocks or [])
        ]
        return resp

    async def create_article(self, user: User, data: ArticleCreate) -> ArticleResponse:
        article_id = f"a_{int(time.time() * 1000)}"
        article = Article(
            id=article_id, author_id=user.id, title=data.title,
            article_type=data.article_type, category_id=data.category_id,
            preview=data.preview, linked_set_id=data.linked_set_id,
            status="draft",
        )
        await self._repo.create(article)

        if data.blocks:
            blocks = [
                ArticleBlock(
                    article_id=article_id, position=b.position, type=b.type,
                    text=b.text, html=b.html, items=b.items, title=b.title,
                )
                for b in data.blocks
            ]
            await self._repo.add_blocks(blocks)

        await self._session.commit()
        self._session.expire_all()
        return await self.get_article(article_id)

    async def update_article(
        self, article_id: str, user: User, data: ArticleUpdate
    ) -> ArticleResponse:
        a = await self._repo.get_by_id(article_id)
        if a is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
        if a.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your article")
        if a.status == "published":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Published articles cannot be edited",
            )

        updates: dict = {}
        if data.title is not None:
            updates["title"] = data.title
        if data.article_type is not None:
            updates["article_type"] = data.article_type
        if data.category_id is not None:
            updates["category_id"] = data.category_id
        if data.preview is not None:
            updates["preview"] = data.preview
        if data.linked_set_id is not None:
            updates["linked_set_id"] = data.linked_set_id

        if updates:
            stmt = sa_update(Article).where(Article.id == article_id).values(**updates)
            await self._session.execute(stmt)

        if data.blocks is not None:
            await self._repo.delete_blocks_by_article(article_id)
            blocks = [
                ArticleBlock(
                    article_id=article_id, position=b.position, type=b.type,
                    text=b.text, html=b.html, items=b.items, title=b.title,
                )
                for b in data.blocks
            ]
            await self._repo.add_blocks(blocks)

        await self._session.commit()
        self._session.expire_all()
        return await self.get_article(article_id)

    async def publish_article(self, article_id: str, user: User) -> ArticleResponse:
        a = await self._repo.get_by_id(article_id)
        if a is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
        if a.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your article")
        if a.status == "published":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already published")

        stmt = sa_update(Article).where(Article.id == article_id).values(
            status="published", published_at=date.today(),
        )
        await self._session.execute(stmt)
        await self._session.commit()
        self._session.expire_all()
        return await self.get_article(article_id)

    async def delete_article(self, article_id: str, user: User) -> None:
        a = await self._repo.get_by_id(article_id)
        if a is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
        if a.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your article")
        await self._repo.delete_article(article_id)
        await self._session.commit()

    async def increment_views(self, article_id: str) -> None:
        stmt = sa_update(Article).where(Article.id == article_id).values(
            views_count=Article.views_count + 1
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def list_comments(
        self, article_id: str, sort: str = "new", limit: int = 50, offset: int = 0
    ) -> tuple[list[ArticleCommentResponse], int]:
        comments, total = await self._repo.list_comments(article_id, sort, limit, offset)
        return [
            ArticleCommentResponse(
                id=c.id, article_id=c.article_id,
                user_id=str(c.user_id) if c.user_id else None,
                initials=c.initials, name=c.name, text=c.text,
                likes_count=c.likes_count, dislikes_count=c.dislikes_count,
                created_at=c.created_at,
            )
            for c in comments
        ], total

    async def add_comment(
        self, article_id: str, user: User, data: ArticleCommentCreate
    ) -> ArticleCommentResponse:
        a = await self._repo.get_by_id(article_id)
        if a is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

        comment = ArticleComment(
            article_id=article_id, user_id=user.id,
            initials=user.initials, name=user.display_name,
            text=data.text,
        )
        comment = await self._repo.add_comment(comment)
        await self._session.commit()
        return ArticleCommentResponse(
            id=comment.id, article_id=comment.article_id,
            user_id=str(comment.user_id),
            initials=comment.initials, name=comment.name,
            text=comment.text, likes_count=comment.likes_count,
            dislikes_count=comment.dislikes_count,
            created_at=comment.created_at,
        )

    async def delete_comment(self, comment_id: int, user: User) -> None:
        comment = await self._repo.get_comment(comment_id)
        if comment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        if comment.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your comment")
        await self._repo.delete_comment(comment_id)
        await self._session.commit()

    async def link_to_set(
        self, article_id: str, user: User, data: ArticleSetLinkCreate
    ) -> None:
        link = ArticleSetLink(
            article_id=article_id, user_id=user.id, set_id=data.set_id,
        )
        await self._repo.link_to_set(link)
        await self._session.commit()

    async def unlink_from_set(self, article_id: str, user: User) -> None:
        await self._repo.unlink_from_set(article_id, user.id)
        await self._session.commit()
