from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select as sa_select

from src.app.core.config import settings
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
    SetPasswordRequest,
    UserResponse,
    VerifyEmailRequest,
)
from src.app.schemas.base import ApiResponse
from src.app.services.auth import AuthService, _user_to_response
from src.app.services.oauth import get_vk_auth_url, get_yandex_auth_url, handle_vk_callback, handle_yandex_callback

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
async def forgot_password(body: ForgotPasswordRequest, session: Session):
    service = AuthService(session)
    await service.forgot_password(body.email)
    return ApiResponse(data=None)


@router.post("/reset-password", response_model=ApiResponse[None])
async def reset_password(body: ResetPasswordRequest, session: Session):
    service = AuthService(session)
    await service.reset_password(body.token, body.password)
    return ApiResponse(data=None)


@router.post("/verify-email", response_model=ApiResponse[None])
async def verify_email(body: VerifyEmailRequest, session: Session):
    service = AuthService(session)
    await service.verify_email(body.token)
    return ApiResponse(data=None)


@router.post("/set-password", response_model=ApiResponse[None])
async def set_password(body: SetPasswordRequest, user: CurrentUser, session: Session):
    service = AuthService(session)
    await service.set_password(user, body.password)
    return ApiResponse(data=None)


@router.get("/oauth/yandex")
async def oauth_yandex():
    return RedirectResponse(get_yandex_auth_url())


@router.get("/oauth/vk")
async def oauth_vk():
    url, _state = get_vk_auth_url()
    return RedirectResponse(url)


@router.get("/link/yandex")
async def link_yandex(token: str = Query(...)):
    from src.app.core.security import decode_token

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return RedirectResponse(get_yandex_auth_url(link_user_id=payload["sub"]))


@router.get("/link/vk")
async def link_vk(token: str = Query(...)):
    from src.app.core.security import decode_token

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    url, _state = get_vk_auth_url(link_user_id=payload["sub"])
    return RedirectResponse(url)


@router.get("/callback/yandex")
async def callback_yandex(session: Session, code: str = Query(...), state: str = Query("")):
    _, tokens = await handle_yandex_callback(code, session, state=state)
    return RedirectResponse(
        f"{settings.frontend_url}/?oauthSuccess=1&accessToken={tokens.access_token}&refreshToken={tokens.refresh_token}"
    )


@router.get("/callback/vk")
async def callback_vk(
    session: Session,
    code: str = Query(...),
    device_id: str = Query(""),
    state: str = Query(""),
):
    _, tokens = await handle_vk_callback(code, device_id, state, session)
    return RedirectResponse(
        f"{settings.frontend_url}/?oauthSuccess=1&accessToken={tokens.access_token}&refreshToken={tokens.refresh_token}"
    )
