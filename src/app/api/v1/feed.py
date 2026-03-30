"""Feed endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_session
from src.app.core.dependencies import get_current_user
from src.app.models.user import User
from src.app.schemas.base import ApiResponse, PaginationMeta
from src.app.schemas.feed import FeedItem
from src.app.services.feed import FeedService

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=ApiResponse[list[FeedItem]])
async def get_feed(
    type: str = Query("all", alias="type"),
    mode: str | None = Query(None),
    category_id: str | None = Query(None, alias="cat"),
    search: str | None = Query(None, alias="q"),
    sort: str = Query("newest"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get unified feed (articles + sets) with filters."""
    service = FeedService(session)
    items, total = await service.get_feed(
        user_id=user.id,
        feed_type=type,
        mode=mode,
        category_id=category_id,
        search=search,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        data=items,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )
