from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_session
from src.app.core.dependencies import get_current_user
from src.app.models.user import User
from src.app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    UserResponse,
)
from src.app.schemas.base import ApiResponse
from src.app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=ApiResponse[AuthResponse], status_code=201)
async def register(body: RegisterRequest, session: AsyncSession = Depends(get_session)):
    service = AuthService(session)
    user, tokens = await service.register(body)
    return ApiResponse(data=AuthResponse(user=user, tokens=tokens))


@router.post("/login", response_model=ApiResponse[AuthResponse])
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)):
    service = AuthService(session)
    user, tokens = await service.login(body)
    return ApiResponse(data=AuthResponse(user=user, tokens=tokens))


@router.post("/refresh", response_model=ApiResponse[RefreshResponse])
async def refresh(body: RefreshRequest, session: AsyncSession = Depends(get_session)):
    service = AuthService(session)
    tokens = await service.refresh(body.refresh_token)
    return ApiResponse(data=RefreshResponse(tokens=tokens))


@router.post("/logout", response_model=ApiResponse[None])
async def logout(_: User = Depends(get_current_user)):
    return ApiResponse(data=None)


@router.get("/me", response_model=ApiResponse[UserResponse])
async def me(user: User = Depends(get_current_user)):
    return ApiResponse(data=UserResponse.model_validate(user))
