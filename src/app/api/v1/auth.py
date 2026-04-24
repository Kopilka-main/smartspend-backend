from fastapi import APIRouter
from sqlalchemy import select as sa_select

from src.app.core.dependencies import CurrentUser, Session
from src.app.models.company import UserCompany
from src.app.repositories.follow import FollowRepository
from src.app.schemas.auth import (
    AuthResponse,
    ChangeEmailRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    ResetPasswordRequest,
    UserResponse,
)
from src.app.schemas.base import ApiResponse
from src.app.services.auth import AuthService, _user_to_response

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=ApiResponse[AuthResponse], status_code=201)
async def register(body: RegisterRequest, session: Session):
    service = AuthService(session)
    user, tokens = await service.register(body)
    return ApiResponse(data=AuthResponse(user=user, tokens=tokens))


@router.post("/login", response_model=ApiResponse[AuthResponse])
async def login(body: LoginRequest, session: Session):
    service = AuthService(session)
    user, tokens = await service.login(body)
    return ApiResponse(data=AuthResponse(user=user, tokens=tokens))


@router.post("/refresh", response_model=ApiResponse[RefreshResponse])
async def refresh(body: RefreshRequest, session: Session):
    service = AuthService(session)
    tokens = await service.refresh(body.refresh_token)
    return ApiResponse(data=RefreshResponse(tokens=tokens))


@router.post("/logout", response_model=ApiResponse[None])
async def logout(_: CurrentUser):
    return ApiResponse(data=None)


@router.get("/me", response_model=ApiResponse[UserResponse])
async def me(user: CurrentUser, session: Session):
    fc = await FollowRepository(session).count_followers(user.id)
    uc_result = await session.execute(sa_select(UserCompany.id).where(UserCompany.user_id == user.id).limit(1))
    has_promo = uc_result.scalar_one_or_none() is not None
    return ApiResponse(data=_user_to_response(user, followers_count=fc, has_promo_setup=has_promo))


@router.post("/change-password", response_model=ApiResponse[None])
async def change_password(body: ChangePasswordRequest, user: CurrentUser, session: Session):
    service = AuthService(session)
    await service.change_password(user, body)
    return ApiResponse(data=None)


@router.post("/change-email", response_model=ApiResponse[None])
async def change_email(body: ChangeEmailRequest, user: CurrentUser, session: Session):
    service = AuthService(session)
    await service.change_email(user, body.new_email, body.password)
    return ApiResponse(data=None)


@router.post("/forgot-password", response_model=ApiResponse[None])
async def forgot_password(body: ForgotPasswordRequest):
    return ApiResponse(data=None)


@router.post("/reset-password", response_model=ApiResponse[None])
async def reset_password(body: ResetPasswordRequest):
    return ApiResponse(data=None)
