"""Follow / subscription endpoints."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_session
from src.app.core.dependencies import get_current_user
from src.app.models.user import User
from src.app.schemas.base import ApiResponse
from src.app.services.follow import FollowService

router = APIRouter(prefix="/users", tags=["follows"])


@router.post("/{user_id}/follow", response_model=ApiResponse[None], status_code=201)
async def follow_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Follow a user."""
    service = FollowService(session)
    await service.follow(current_user, user_id)
    return ApiResponse(data=None)


@router.delete("/{user_id}/follow", response_model=ApiResponse[None])
async def unfollow_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Unfollow a user."""
    service = FollowService(session)
    await service.unfollow(current_user.id, user_id)
    return ApiResponse(data=None)
