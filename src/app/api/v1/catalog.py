"""Catalog / sets endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_session
from src.app.core.dependencies import get_current_user
from src.app.models.user import User
from src.app.schemas.base import ApiResponse, PaginationMeta
from src.app.schemas.catalog import (
    SetCommentCreate,
    SetCommentResponse,
    SetCreate,
    SetListItem,
    SetResponse,
    SetUpdate,
)
from src.app.services.catalog import CatalogService

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("", response_model=ApiResponse[list[SetListItem]])
async def list_sets(
    category_id: str | None = Query(None),
    source: str | None = Query(None),
    set_type: str | None = Query(None),
    search: str | None = Query(None, alias="q"),
    sort: str = Query("newest"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List public catalog sets with filters."""
    service = CatalogService(session)
    items, total = await service.list_sets(
        category_id=category_id,
        source=source,
        set_type=set_type,
        search=search,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        data=items,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.get("/{set_id}", response_model=ApiResponse[SetResponse])
async def get_set(set_id: str, session: AsyncSession = Depends(get_session)):
    """Get full set details with items."""
    service = CatalogService(session)
    result = await service.get_set(set_id)
    return ApiResponse(data=result)


@router.post("", response_model=ApiResponse[SetResponse], status_code=201)
async def create_set(
    body: SetCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new set."""
    service = CatalogService(session)
    result = await service.create_set(user, body)
    return ApiResponse(data=result)


@router.put("/{set_id}", response_model=ApiResponse[SetResponse])
async def update_set(
    set_id: str,
    body: SetUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update a private set."""
    service = CatalogService(session)
    result = await service.update_set(set_id, user, body)
    return ApiResponse(data=result)


@router.put("/{set_id}/hide", response_model=ApiResponse[None])
async def hide_set(
    set_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Hide a public set from catalog."""
    service = CatalogService(session)
    await service.hide_set(set_id, user)
    return ApiResponse(data=None)


@router.delete("/{set_id}", response_model=ApiResponse[None])
async def delete_set(
    set_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a private set."""
    service = CatalogService(session)
    await service.delete_set(set_id, user)
    return ApiResponse(data=None)


# --- comments ---


@router.get("/{set_id}/comments", response_model=ApiResponse[list[SetCommentResponse]])
async def list_comments(
    set_id: str,
    sort: str = Query("new"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List comments for a set."""
    service = CatalogService(session)
    comments, total = await service.list_comments(set_id, sort, limit, offset)
    return ApiResponse(
        data=comments,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.post(
    "/{set_id}/comments", response_model=ApiResponse[SetCommentResponse], status_code=201
)
async def add_comment(
    set_id: str,
    body: SetCommentCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add a comment to a set."""
    service = CatalogService(session)
    comment = await service.add_comment(set_id, user, body)
    return ApiResponse(data=comment)


@router.delete("/comments/{comment_id}", response_model=ApiResponse[None])
async def delete_comment(
    comment_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete own comment on a set."""
    service = CatalogService(session)
    await service.delete_comment(comment_id, user)
    return ApiResponse(data=None)
