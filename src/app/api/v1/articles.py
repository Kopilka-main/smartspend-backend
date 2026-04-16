import uuid

from fastapi import APIRouter, Query, UploadFile

from src.app.core.dependencies import CurrentUser, OptionalUser, Session
from src.app.schemas.article import (
    ArticleCommentCreate,
    ArticleCommentResponse,
    ArticleCreate,
    ArticleListItem,
    ArticlePhotoResponse,
    ArticleResponse,
    ArticleSetLinkCreate,
    ArticleUpdate,
)
from src.app.schemas.base import ApiResponse, PaginationMeta
from src.app.services.article import ArticleService

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=ApiResponse[list[ArticleListItem]])
async def list_articles(
    session: Session,
    category_id: str | None = Query(None),
    author_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None, alias="q"),
    sort: str = Query("newest"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
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
    user: CurrentUser,
    session: Session,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    service = ArticleService(session)
    items, total = await service.list_by_author(user.id, limit, offset)
    return ApiResponse(
        data=items,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.get("/{article_id}", response_model=ApiResponse[ArticleResponse])
async def get_article(article_id: str, session: Session):
    service = ArticleService(session)
    return ApiResponse(data=await service.get_article(article_id))


@router.post("", response_model=ApiResponse[ArticleResponse], status_code=201)
async def create_article(body: ArticleCreate, user: CurrentUser, session: Session):
    service = ArticleService(session)
    return ApiResponse(data=await service.create_article(user, body))


@router.put("/{article_id}", response_model=ApiResponse[ArticleResponse])
async def update_article(article_id: str, body: ArticleUpdate, user: CurrentUser, session: Session):
    service = ArticleService(session)
    return ApiResponse(data=await service.update_article(article_id, user, body))


@router.post("/{article_id}/publish", response_model=ApiResponse[ArticleResponse])
async def publish_article(article_id: str, user: CurrentUser, session: Session):
    service = ArticleService(session)
    return ApiResponse(data=await service.publish_article(article_id, user))


@router.delete("/{article_id}", response_model=ApiResponse[None])
async def delete_article(article_id: str, user: CurrentUser, session: Session):
    service = ArticleService(session)
    await service.delete_article(article_id, user)
    return ApiResponse(data=None)


@router.post("/{article_id}/read", response_model=ApiResponse[None])
async def mark_read(article_id: str, session: Session, user: OptionalUser):
    service = ArticleService(session)
    await service.mark_read(article_id, user.id if user else None)
    return ApiResponse(data=None)


@router.get("/{article_id}/comments", response_model=ApiResponse[list[ArticleCommentResponse]])
async def list_comments(
    article_id: str,
    session: Session,
    sort: str = Query("new"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    service = ArticleService(session)
    comments, total = await service.list_comments(article_id, sort, limit, offset)
    return ApiResponse(
        data=comments,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.post("/{article_id}/comments", response_model=ApiResponse[ArticleCommentResponse], status_code=201)
async def add_comment(article_id: str, body: ArticleCommentCreate, user: CurrentUser, session: Session):
    service = ArticleService(session)
    return ApiResponse(data=await service.add_comment(article_id, user, body))


@router.delete("/comments/{comment_id}", response_model=ApiResponse[None])
async def delete_comment(comment_id: int, user: CurrentUser, session: Session):
    service = ArticleService(session)
    await service.delete_comment(comment_id, user)
    return ApiResponse(data=None)


@router.post("/{article_id}/link-set", response_model=ApiResponse[None], status_code=201)
async def link_to_set(article_id: str, body: ArticleSetLinkCreate, user: CurrentUser, session: Session):
    service = ArticleService(session)
    await service.link_to_set(article_id, user, body)
    return ApiResponse(data=None)


@router.delete("/{article_id}/link-set", response_model=ApiResponse[None])
async def unlink_from_set(article_id: str, user: CurrentUser, session: Session):
    service = ArticleService(session)
    await service.unlink_from_set(article_id, user)
    return ApiResponse(data=None)


@router.post("/{article_id}/photos", response_model=ApiResponse[ArticlePhotoResponse], status_code=201)
async def add_article_photo(article_id: str, file: UploadFile, user: CurrentUser, session: Session):
    service = ArticleService(session)
    return ApiResponse(data=await service.add_photo(article_id, user, file))


@router.delete("/photos/{photo_id}", response_model=ApiResponse[None])
async def delete_article_photo(photo_id: int, user: CurrentUser, session: Session):
    service = ArticleService(session)
    await service.delete_photo(photo_id, user)
    return ApiResponse(data=None)
