from fastapi import APIRouter, Query

from src.app.core.dependencies import CurrentUser, OptionalUser, Session
from src.app.schemas.base import ApiResponse, PaginationMeta
from src.app.schemas.promo import (
    PromoCommentCreate,
    PromoCommentResponse,
    PromoCreate,
    PromoResponse,
    PromoVoteRequest,
)
from src.app.services.promo import PromoService

router = APIRouter(prefix="/promos", tags=["promos"])


@router.get("", response_model=ApiResponse[list[PromoResponse]])
async def list_promos(
    session: Session,
    current_user: OptionalUser,
    type: str | None = Query(None),
    scope: str = Query("all"),
    category_ids: str | None = Query(None, alias="categoryIds"),
    company_ids: str | None = Query(None, alias="companyIds"),
    promo_filter: str | None = Query(None, alias="promoFilter"),
    search: str | None = Query(None, alias="q"),
    sort: str = Query("newest"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    user_id = current_user.id if current_user else None
    cats = [c.strip() for c in category_ids.split(",") if c.strip()] if category_ids else None
    cos = [c.strip() for c in company_ids.split(",") if c.strip()] if company_ids else None
    service = PromoService(session)
    items, total = await service.list_promos(
        promo_type=type,
        scope=scope,
        category_ids=cats,
        company_ids=cos,
        promo_filter=promo_filter,
        search=search,
        sort=sort,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        data=items,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.get("/{promo_id}", response_model=ApiResponse[PromoResponse])
async def get_promo(promo_id: int, session: Session):
    service = PromoService(session)
    return ApiResponse(data=await service.get_promo(promo_id))


@router.post("", response_model=ApiResponse[PromoResponse], status_code=201)
async def create_promo(body: PromoCreate, user: CurrentUser, session: Session):
    service = PromoService(session)
    return ApiResponse(data=await service.create_promo(user, body))


@router.post("/{promo_id}/vote", response_model=ApiResponse[PromoResponse])
async def vote_promo(promo_id: int, body: PromoVoteRequest, user: CurrentUser, session: Session):
    service = PromoService(session)
    return ApiResponse(data=await service.vote(promo_id, user.id, body.vote))


@router.get("/{promo_id}/comments", response_model=ApiResponse[list[PromoCommentResponse]])
async def list_promo_comments(
    promo_id: int,
    session: Session,
    sort: str = Query("new"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    service = PromoService(session)
    comments, total = await service.list_comments(promo_id, sort, limit, offset)
    return ApiResponse(
        data=comments,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.post("/{promo_id}/comments", response_model=ApiResponse[PromoCommentResponse], status_code=201)
async def add_promo_comment(promo_id: int, body: PromoCommentCreate, user: CurrentUser, session: Session):
    service = PromoService(session)
    return ApiResponse(data=await service.add_comment(promo_id, user, body))


@router.delete("/comments/{comment_id}", response_model=ApiResponse[None])
async def delete_promo_comment(comment_id: int, user: CurrentUser, session: Session):
    service = PromoService(session)
    await service.delete_comment(comment_id, user.id)
    return ApiResponse(data=None)
