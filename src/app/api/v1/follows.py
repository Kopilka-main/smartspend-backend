import uuid

from fastapi import APIRouter

from src.app.core.dependencies import CurrentUser, Session
from src.app.schemas.base import ApiResponse
from src.app.schemas.user import AuthorInfo
from src.app.services.follow import FollowService

router = APIRouter(prefix="/users", tags=["follows"])


@router.get("/me/following", response_model=ApiResponse[list[AuthorInfo]])
async def list_following(current_user: CurrentUser, session: Session):
    service = FollowService(session)
    return ApiResponse(data=await service.list_following(current_user.id))


@router.get("/me/followers", response_model=ApiResponse[list[AuthorInfo]])
async def list_followers(current_user: CurrentUser, session: Session):
    service = FollowService(session)
    return ApiResponse(data=await service.list_followers(current_user.id))


@router.post("/{user_id}/follow", response_model=ApiResponse[None], status_code=201)
async def follow_user(user_id: uuid.UUID, current_user: CurrentUser, session: Session):
    service = FollowService(session)
    await service.follow(current_user, user_id)
    return ApiResponse(data=None)


@router.delete("/{user_id}/follow", response_model=ApiResponse[None])
async def unfollow_user(user_id: uuid.UUID, current_user: CurrentUser, session: Session):
    service = FollowService(session)
    await service.unfollow(current_user.id, user_id)
    return ApiResponse(data=None)
