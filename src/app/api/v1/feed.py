from fastapi import APIRouter, Query

from src.app.core.dependencies import CurrentUser, Session
from src.app.schemas.base import ApiResponse, PaginationMeta
from src.app.schemas.feed import FeedItem
from src.app.services.feed import FeedService

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=ApiResponse[list[FeedItem]])
async def get_feed(
    user: CurrentUser,
    session: Session,
    mode: str | None = Query(None),
    category_ids: str | None = Query(None, alias="cat"),
    search: str | None = Query(None, alias="q"),
    sort: str = Query("popular_7d"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    cats = [c.strip() for c in category_ids.split(",") if c.strip()] if category_ids else None
    service = FeedService(session)
    items, total = await service.get_feed(
        user_id=user.id,
        mode=mode,
        category_ids=cats,
        search=search,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        data=items,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.get("/tags", response_model=ApiResponse[list[str]])
async def get_tags(session: Session):
    service = FeedService(session)
    return ApiResponse(data=await service.get_tags())
