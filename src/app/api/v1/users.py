import uuid

from fastapi import APIRouter

from src.app.core.dependencies import CurrentUser, OptionalUser, Session
from src.app.schemas.auth import UserResponse
from src.app.schemas.base import ApiResponse
from src.app.schemas.user import (
    DeleteAccountRequest,
    ProfileSummary,
    ProfileUpdate,
    SettingsResponse,
    SettingsUpdate,
    UserFinanceResponse,
    UserFinanceUpdate,
    UserPublicResponse,
)
from src.app.services.user import UserService

router = APIRouter(tags=["users"])


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_me(user: CurrentUser, session: Session):
    service = UserService(session)
    result = await service.get_profile(user)
    return ApiResponse(data=result)


@router.put("/me", response_model=ApiResponse[UserResponse])
async def update_me(body: ProfileUpdate, user: CurrentUser, session: Session):
    service = UserService(session)
    updated = await service.update_profile(user, body)
    return ApiResponse(data=updated)


@router.get("/me/settings", response_model=ApiResponse[SettingsResponse])
async def get_settings(user: CurrentUser):
    return ApiResponse(
        data=SettingsResponse(
            theme=user.theme,
            timezone=user.timezone,
            location=user.location,
            notify_new_sets=user.notify_new_sets,
            notify_author_articles=user.notify_author_articles,
            notify_subscriptions=user.notify_subscriptions,
            notify_set_changes=user.notify_set_changes,
            notify_reminders=user.notify_reminders,
            privacy_sets=user.privacy_sets,
            privacy_articles=user.privacy_articles,
            privacy_profile=user.privacy_profile,
        )
    )


@router.put("/me/settings", response_model=ApiResponse[UserResponse])
async def update_settings(body: SettingsUpdate, user: CurrentUser, session: Session):
    service = UserService(session)
    updated = await service.update_settings(user, body)
    return ApiResponse(data=updated)


@router.delete("/me", response_model=ApiResponse[None])
async def delete_account(body: DeleteAccountRequest, user: CurrentUser, session: Session):
    service = UserService(session)
    await service.delete_account(user, body)
    return ApiResponse(data=None)


@router.put("/me/cancel-deletion", response_model=ApiResponse[UserResponse])
async def cancel_deletion(user: CurrentUser, session: Session):
    service = UserService(session)
    updated = await service.cancel_deletion(user)
    return ApiResponse(data=updated)


@router.get("/profile/finance", response_model=ApiResponse[UserFinanceResponse])
async def get_finance(user: CurrentUser, session: Session):
    service = UserService(session)
    finance = await service.get_finance(user.id)
    return ApiResponse(data=finance)


@router.put("/profile/finance", response_model=ApiResponse[UserFinanceResponse])
async def update_finance(body: UserFinanceUpdate, user: CurrentUser, session: Session):
    service = UserService(session)
    finance = await service.update_finance(user.id, body)
    return ApiResponse(data=finance)


@router.get("/profile/summary", response_model=ApiResponse[ProfileSummary])
async def get_summary(user: CurrentUser, session: Session):
    service = UserService(session)
    summary = await service.get_summary(user.id)
    return ApiResponse(data=summary)


@router.get("/users/{user_id}", response_model=ApiResponse[UserPublicResponse])
async def get_public_profile(user_id: uuid.UUID, session: Session, current_user: OptionalUser):
    service = UserService(session)
    viewer_id = current_user.id if current_user else None
    profile = await service.get_public_profile(user_id, viewer_id)
    return ApiResponse(data=profile)
