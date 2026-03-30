"""Notification endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_session
from src.app.core.dependencies import get_current_user
from src.app.models.user import User
from src.app.schemas.base import ApiResponse, PaginationMeta
from src.app.schemas.notification import NotificationResponse
from src.app.services.notification import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=ApiResponse[list[NotificationResponse]])
async def list_notifications(
    type: str | None = Query(None, alias="type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List notifications for current user."""
    service = NotificationService(session)
    notifs, total = await service.list_notifications(user.id, type, limit, offset)
    return ApiResponse(
        data=notifs,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.get("/unread-count", response_model=ApiResponse[int])
async def unread_count(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get count of unread notifications."""
    service = NotificationService(session)
    count = await service.count_unread(user.id)
    return ApiResponse(data=count)


@router.post("/{notification_id}/read", response_model=ApiResponse[None])
async def mark_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Mark a notification as read."""
    service = NotificationService(session)
    await service.mark_read(notification_id, user.id)
    return ApiResponse(data=None)


@router.post("/read-all", response_model=ApiResponse[None])
async def mark_all_read(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Mark all notifications as read."""
    service = NotificationService(session)
    await service.mark_all_read(user.id)
    return ApiResponse(data=None)
