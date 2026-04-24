from fastapi import APIRouter, Query, UploadFile

from src.app.core.dependencies import CurrentUser, OptionalUser, Session
from src.app.schemas.base import ApiResponse, PaginationMeta
from src.app.schemas.catalog import (
    SetCommentCreate,
    SetCommentResponse,
    SetCreate,
    SetListItem,
    SetPhotoResponse,
    SetResponse,
    SetUpdate,
)
from src.app.services.article import ArticleService
from src.app.services.catalog import CatalogService

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("", response_model=ApiResponse[list[SetListItem]])
async def list_sets(
    session: Session,
    current_user: OptionalUser,
    category_ids: str | None = Query(None),
    source: str | None = Query(None),
    set_type: str | None = Query(None),
    search: str | None = Query(None, alias="q"),
    sort: str = Query("newest"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    user_id = current_user.id if current_user else None
    cats = [c.strip() for c in category_ids.split(",") if c.strip()] if category_ids else None
    service = CatalogService(session)
    items, total = await service.list_sets(
        category_ids=cats,
        source=source,
        set_type=set_type,
        search=search,
        sort=sort,
        limit=limit,
        offset=offset,
        user_id=user_id,
    )
    return ApiResponse(
        data=items,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.get("/my", response_model=ApiResponse[list[SetListItem]])
async def list_my_sets(user: CurrentUser, session: Session):
    service = CatalogService(session)
    items, _total = await service.list_by_author(user.id)
    return ApiResponse(data=items)


@router.get("/{set_id}", response_model=ApiResponse[SetResponse])
async def get_set(set_id: str, session: Session):
    service = CatalogService(session)
    return ApiResponse(data=await service.get_set(set_id))


@router.post("", response_model=ApiResponse[SetResponse], status_code=201)
async def create_set(body: SetCreate, user: CurrentUser, session: Session):
    service = CatalogService(session)
    return ApiResponse(data=await service.create_set(user, body))


@router.put("/{set_id}", response_model=ApiResponse[SetResponse])
async def update_set(set_id: str, body: SetUpdate, user: CurrentUser, session: Session):
    service = CatalogService(session)
    return ApiResponse(data=await service.update_set(set_id, user, body))


@router.put("/{set_id}/hide", response_model=ApiResponse[None])
async def hide_set(set_id: str, user: CurrentUser, session: Session):
    service = CatalogService(session)
    await service.hide_set(set_id, user)
    return ApiResponse(data=None)


@router.delete("/{set_id}", response_model=ApiResponse[None])
async def delete_set(set_id: str, user: CurrentUser, session: Session):
    service = CatalogService(session)
    await service.delete_set(set_id, user)
    return ApiResponse(data=None)


@router.get("/{set_id}/comments", response_model=ApiResponse[list[SetCommentResponse]])
async def list_comments(
    set_id: str,
    session: Session,
    sort: str = Query("new"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    service = CatalogService(session)
    comments, total = await service.list_comments(set_id, sort, limit, offset)
    return ApiResponse(
        data=comments,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.post("/{set_id}/comments", response_model=ApiResponse[SetCommentResponse], status_code=201)
async def add_comment(set_id: str, body: SetCommentCreate, user: CurrentUser, session: Session):
    service = CatalogService(session)
    return ApiResponse(data=await service.add_comment(set_id, user, body))


@router.delete("/comments/{comment_id}", response_model=ApiResponse[None])
async def delete_comment(comment_id: int, user: CurrentUser, session: Session):
    service = CatalogService(session)
    await service.delete_comment(comment_id, user)
    return ApiResponse(data=None)


@router.get("/{set_id}/articles", response_model=ApiResponse[list])
async def get_set_articles(set_id: str, session: Session):
    service = ArticleService(session)
    items, _total = await service.list_published(linked_set_id=set_id)
    return ApiResponse(data=items)


@router.post("/{set_id}/photos", response_model=ApiResponse[SetPhotoResponse], status_code=201)
async def add_set_photo(set_id: str, file: UploadFile, user: CurrentUser, session: Session):
    service = CatalogService(session)
    return ApiResponse(data=await service.add_photo(set_id, user, file))


@router.delete("/photos/{photo_id}", response_model=ApiResponse[None])
async def delete_set_photo(photo_id: int, user: CurrentUser, session: Session):
    service = CatalogService(session)
    await service.delete_photo(photo_id, user)
    return ApiResponse(data=None)


@router.post("/{set_id}/bookmark", response_model=ApiResponse[None], status_code=201)
async def bookmark_set(set_id: str, user: CurrentUser, session: Session):
    service = CatalogService(session)
    await service.bookmark(set_id, user.id)
    return ApiResponse(data=None)


@router.delete("/{set_id}/bookmark", response_model=ApiResponse[None])
async def unbookmark_set(set_id: str, user: CurrentUser, session: Session):
    service = CatalogService(session)
    await service.unbookmark(set_id, user.id)
    return ApiResponse(data=None)
