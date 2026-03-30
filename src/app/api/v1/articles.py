"""Article endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_session
from src.app.core.dependencies import get_current_user
from src.app.models.user import User
from src.app.schemas.article import (
    ArticleCommentCreate,
    ArticleCommentResponse,
    ArticleCreate,
    ArticleListItem,
    ArticleResponse,
    ArticleSetLinkCreate,
    ArticleUpdate,
)
from src.app.schemas.base import ApiResponse, PaginationMeta
from src.app.services.article import ArticleService

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=ApiResponse[list[ArticleListItem]])
async def list_articles(
    category_id: str | None = Query(None),
    author_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None, alias="q"),
    sort: str = Query("newest"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List published articles."""
    service = ArticleService(session)
    items, total = await service.list_published(
        category_id=category_id,
        author_id=author_id,
        search=search,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        data=items,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.get("/my", response_model=ApiResponse[list[ArticleListItem]])
async def list_my_articles(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List current user's articles (including drafts)."""
    service = ArticleService(session)
    items, total = await service.list_by_author(user.id, limit, offset)
    return ApiResponse(
        data=items,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.get("/{article_id}", response_model=ApiResponse[ArticleResponse])
async def get_article(article_id: str, session: AsyncSession = Depends(get_session)):
    """Get full article with blocks."""
    service = ArticleService(session)
    result = await service.get_article(article_id)
    return ApiResponse(data=result)


@router.post("", response_model=ApiResponse[ArticleResponse], status_code=201)
async def create_article(
    body: ArticleCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a draft article."""
    service = ArticleService(session)
    result = await service.create_article(user, body)
    return ApiResponse(data=result)


@router.put("/{article_id}", response_model=ApiResponse[ArticleResponse])
async def update_article(
    article_id: str,
    body: ArticleUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update a draft article."""
    service = ArticleService(session)
    result = await service.update_article(article_id, user, body)
    return ApiResponse(data=result)


@router.post("/{article_id}/publish", response_model=ApiResponse[ArticleResponse])
async def publish_article(
    article_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Publish a draft article."""
    service = ArticleService(session)
    result = await service.publish_article(article_id, user)
    return ApiResponse(data=result)


@router.delete("/{article_id}", response_model=ApiResponse[None])
async def delete_article(
    article_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete an article."""
    service = ArticleService(session)
    await service.delete_article(article_id, user)
    return ApiResponse(data=None)


@router.post("/{article_id}/read", response_model=ApiResponse[None])
async def mark_read(
    article_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Increment article view count."""
    service = ArticleService(session)
    await service.increment_views(article_id)
    return ApiResponse(data=None)


# --- comments ---


@router.get("/{article_id}/comments", response_model=ApiResponse[list[ArticleCommentResponse]])
async def list_comments(
    article_id: str,
    sort: str = Query("new"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List comments for an article."""
    service = ArticleService(session)
    comments, total = await service.list_comments(article_id, sort, limit, offset)
    return ApiResponse(
        data=comments,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.post(
    "/{article_id}/comments",
    response_model=ApiResponse[ArticleCommentResponse],
    status_code=201,
)
async def add_comment(
    article_id: str,
    body: ArticleCommentCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add a comment to an article."""
    service = ArticleService(session)
    comment = await service.add_comment(article_id, user, body)
    return ApiResponse(data=comment)


@router.delete("/comments/{comment_id}", response_model=ApiResponse[None])
async def delete_comment(
    comment_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete own comment on an article."""
    service = ArticleService(session)
    await service.delete_comment(comment_id, user)
    return ApiResponse(data=None)


# --- article-set links ---


@router.post("/{article_id}/link-set", response_model=ApiResponse[None], status_code=201)
async def link_to_set(
    article_id: str,
    body: ArticleSetLinkCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Link an article to a user's set."""
    service = ArticleService(session)
    await service.link_to_set(article_id, user, body)
    return ApiResponse(data=None)


@router.delete("/{article_id}/link-set", response_model=ApiResponse[None])
async def unlink_from_set(
    article_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Remove article-set link."""
    service = ArticleService(session)
    await service.unlink_from_set(article_id, user)
    return ApiResponse(data=None)
