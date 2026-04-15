import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.app.models.enums import UserStatus
from src.app.models.user import User
from src.app.models.user_finance import UserFinance
from src.app.repositories.follow import FollowRepository
from src.app.repositories.user import UserRepository
from src.app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenPair,
    UserFinanceInline,
    UserResponse,
)


def _build_initials(display_name: str) -> str:
    parts = display_name.strip().split()
    return "".join(p[0] for p in parts if p)[:2].upper() or "??"


def _user_to_response(user: User, followers_count: int = 0) -> UserResponse:
    finance_data = None
    if user.finance:
        finance_data = UserFinanceInline(
            income=user.finance.income,
            housing=user.finance.housing,
            credit=user.finance.credit,
            credit_months=user.finance.credit_months,
            capital=user.finance.capital,
            emo_rate=user.finance.emo_rate,
        )
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        username=user.username,
        initials=user.initials,
        color=user.color,
        bio=user.bio,
        avatar_url=user.avatar_url,
        status=user.status,
        theme=user.theme,
        joined_at=user.joined_at,
        followers_count=followers_count,
        finance=finance_data,
    )


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = UserRepository(session)

    async def register(self, data: RegisterRequest) -> tuple[UserResponse, TokenPair]:
        existing = await self._repo.get_by_email(data.email)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            display_name=data.display_name,
            initials=_build_initials(data.display_name),
        )
        finance = UserFinance(user_id=user.id)

        await self._repo.create(user, finance)
        await self._session.commit()

        tokens = self._issue_tokens(user.id)
        return _user_to_response(user), tokens

    async def login(self, data: LoginRequest) -> tuple[UserResponse, TokenPair]:
        user = await self._repo.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

        if user.status == UserStatus.SUSPENDED:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")

        if user.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account pending deletion")

        tokens = self._issue_tokens(user.id)
        follow_repo = FollowRepository(self._session)
        fc = await follow_repo.count_followers(user.id)
        return _user_to_response(user, followers_count=fc), tokens

    async def refresh(self, refresh_token: str) -> TokenPair:
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        try:
            user_id = uuid.UUID(payload["sub"])
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload") from exc

        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        return self._issue_tokens(user.id)

    async def change_password(self, user: User, data: ChangePasswordRequest) -> None:
        if not verify_password(data.current_password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
        await self._repo.update_fields(user.id, password_hash=hash_password(data.new_password))
        await self._session.commit()

    @staticmethod
    def _issue_tokens(user_id: uuid.UUID) -> TokenPair:
        return TokenPair(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
        )
