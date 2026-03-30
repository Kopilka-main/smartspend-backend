import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_session
from src.app.core.dependencies import get_current_user, get_optional_user
from src.app.models.user import User
from src.app.schemas.auth import UserResponse
from src.app.schemas.base import ApiResponse
from src.app.schemas.user import (
    DeleteAccountRequest,
    ProfileSummary,
    ProfileUpdate,
    SettingsUpdate,
    UserFinanceResponse,
    UserFinanceUpdate,
    UserPublicResponse,
)
from src.app.services.user import UserService

router = APIRouter(tags=["users"])


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_me(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    result = await service.get_profile(user)
    return ApiResponse(data=result)


@router.put("/me", response_model=ApiResponse[UserResponse])
async def update_me(
    body: ProfileUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    updated = await service.update_profile(user, body)
    return ApiResponse(data=updated)


@router.put("/me/settings", response_model=ApiResponse[UserResponse])
async def update_settings(
    body: SettingsUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    updated = await service.update_settings(user, body)
    return ApiResponse(data=updated)


@router.delete("/me", response_model=ApiResponse[None])
async def delete_account(
    body: DeleteAccountRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    await service.delete_account(user, body)
    return ApiResponse(data=None)


@router.put("/me/cancel-deletion", response_model=ApiResponse[UserResponse])
async def cancel_deletion(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    updated = await service.cancel_deletion(user)
    return ApiResponse(data=updated)


@router.get("/profile/finance", response_model=ApiResponse[UserFinanceResponse])
async def get_finance(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    finance = await service.get_finance(user.id)
    return ApiResponse(data=finance)


@router.put("/profile/finance", response_model=ApiResponse[UserFinanceResponse])
async def update_finance(
    body: UserFinanceUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    finance = await service.update_finance(user.id, body)
    return ApiResponse(data=finance)


@router.get("/profile/summary", response_model=ApiResponse[ProfileSummary])
async def get_summary(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = UserService(session)
    summary = await service.get_summary(user.id)
    return ApiResponse(data=summary)


@router.get("/users/{user_id}", response_model=ApiResponse[UserPublicResponse])
async def get_public_profile(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_optional_user),
):
    service = UserService(session)
    viewer_id = current_user.id if current_user else None
    profile = await service.get_public_profile(user_id, viewer_id)
    return ApiResponse(data=profile)
