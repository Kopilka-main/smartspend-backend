from fastapi import APIRouter, Query

from src.app.core.dependencies import CurrentUser, Session
from src.app.schemas.base import ApiResponse, PaginationMeta
from src.app.schemas.notification import (
    NotificationMessageCreate,
    NotificationMessageResponse,
    NotificationResponse,
)
from src.app.services.notification import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=ApiResponse[list[NotificationResponse]])
async def list_notifications(
    user: CurrentUser,
    session: Session,
    type: str | None = Query(None, alias="type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    service = NotificationService(session)
    notifs, total = await service.list_notifications(user.id, type, limit, offset)
    return ApiResponse(
        data=notifs,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.get("/unread-count", response_model=ApiResponse[int])
async def unread_count(user: CurrentUser, session: Session):
    service = NotificationService(session)
    return ApiResponse(data=await service.count_unread(user.id))


@router.post("/{notification_id}/read", response_model=ApiResponse[None])
async def mark_read(notification_id: int, user: CurrentUser, session: Session):
    service = NotificationService(session)
    await service.mark_read(notification_id, user.id)
    return ApiResponse(data=None)


@router.post("/read-all", response_model=ApiResponse[None])
async def mark_all_read(user: CurrentUser, session: Session):
    service = NotificationService(session)
    await service.mark_all_read(user.id)
    return ApiResponse(data=None)


@router.post("/{notification_id}/approve", response_model=ApiResponse[None])
async def approve_request(notification_id: int, user: CurrentUser, session: Session):
    service = NotificationService(session)
    await service.set_action(notification_id, user.id, "approved")
    return ApiResponse(data=None)


@router.post("/{notification_id}/reject", response_model=ApiResponse[None])
async def reject_request(notification_id: int, user: CurrentUser, session: Session):
    service = NotificationService(session)
    await service.set_action(notification_id, user.id, "rejected")
    return ApiResponse(data=None)


@router.post(
    "/{notification_id}/messages",
    response_model=ApiResponse[NotificationMessageResponse],
    status_code=201,
)
async def add_message(notification_id: int, body: NotificationMessageCreate, user: CurrentUser, session: Session):
    service = NotificationService(session)
    return ApiResponse(data=await service.add_message(notification_id, user.id, body.text))


@router.get(
    "/{notification_id}/messages",
    response_model=ApiResponse[list[NotificationMessageResponse]],
)
async def list_messages(notification_id: int, user: CurrentUser, session: Session):
    service = NotificationService(session)
    return ApiResponse(data=await service.list_messages(notification_id, user.id))


@router.post("/{notification_id}/withdraw", response_model=ApiResponse[None])
async def withdraw_request(notification_id: int, user: CurrentUser, session: Session):
    service = NotificationService(session)
    await service.withdraw(notification_id, user.id)
    return ApiResponse(data=None)
