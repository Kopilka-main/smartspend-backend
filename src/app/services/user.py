import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.security import verify_password
from src.app.models.company import UserCompany
from src.app.models.enums import UserStatus
from src.app.models.user import User
from src.app.repositories.article import ArticleRepository
from src.app.repositories.catalog import CatalogRepository
from src.app.repositories.envelope import EnvelopeRepository
from src.app.repositories.follow import FollowRepository
from src.app.repositories.user import UserRepository
from src.app.schemas.auth import UserResponse
from src.app.schemas.user import (
    DeleteAccountRequest,
    ProfileSummary,
    ProfileUpdate,
    SettingsUpdate,
    UserFinanceResponse,
    UserFinanceUpdate,
    UserPublicResponse,
)
from src.app.services.auth import _user_to_response


def _build_initials(display_name: str) -> str:
    parts = display_name.strip().split()
    return "".join(p[0] for p in parts if p)[:2].upper() or "??"


BASE_RETURN_ANNUAL = Decimal("0.12")


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = UserRepository(session)

    async def get_profile(self, user: User) -> UserResponse:
        follow_repo = FollowRepository(self._session)
        fc = await follow_repo.count_followers(user.id)
        uc_result = await self._session.execute(
            sa_select(UserCompany.id).where(UserCompany.user_id == user.id).limit(1)
        )
        has_promo = uc_result.scalar_one_or_none() is not None
        providers = await self._load_providers(user.id)
        return _user_to_response(user, followers_count=fc, has_promo_setup=has_promo, oauth_providers=providers)

    async def _load_providers(self, user_id) -> list[str]:
        from src.app.models.user_oauth_link import UserOAuthLink

        result = await self._session.execute(sa_select(UserOAuthLink.provider).where(UserOAuthLink.user_id == user_id))
        return [row[0] for row in result.all()]

    async def update_profile(self, user: User, data: ProfileUpdate) -> UserResponse:
        updates: dict = {}
        if data.display_name is not None:
            updates["display_name"] = data.display_name
            updates["initials"] = _build_initials(data.display_name)
        if data.username is not None:
            existing = await self._repo.get_by_username(data.username)
            if existing and existing.id != user.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
            updates["username"] = data.username
        if data.bio is not None:
            updates["bio"] = data.bio
        if updates:
            await self._repo.update_fields(user.id, **updates)
            await self._session.commit()
            refreshed = await self._repo.get_by_id(user.id)
            return _user_to_response(refreshed)
        return _user_to_response(user)

    async def update_settings(self, user: User, data: SettingsUpdate) -> UserResponse:
        updates = data.model_dump(exclude_unset=True)
        if updates:
            await self._repo.update_fields(user.id, **updates)
            await self._session.commit()
            refreshed = await self._repo.get_by_id(user.id)
            return _user_to_response(refreshed)
        return _user_to_response(user)

    async def get_finance(self, user_id: uuid.UUID) -> UserFinanceResponse:
        finance = await self._repo.get_finance(user_id)
        if finance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finance data not found")
        return UserFinanceResponse.model_validate(finance)

    async def update_finance(self, user_id: uuid.UUID, data: UserFinanceUpdate) -> UserFinanceResponse:
        updates = data.model_dump(exclude_unset=True)
        if updates:
            await self._repo.update_finance(user_id, **updates)
            await self._session.commit()
        self._session.expire_all()
        finance = await self._repo.get_finance(user_id)
        return UserFinanceResponse.model_validate(finance)

    async def get_summary(self, user_id: uuid.UUID) -> ProfileSummary:
        finance = await self._repo.get_finance(user_id)
        if finance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finance data not found")

        envelope_repo = EnvelopeRepository(self._session)
        smart_base = await envelope_repo.sum_amount_by_user(user_id)

        emo_spend = int(Decimal(finance.capital) * finance.emo_rate / 12)
        free_remainder = finance.income - finance.housing - finance.credit - smart_base - emo_spend
        capital_growth = int(Decimal(finance.capital) * BASE_RETURN_ANNUAL / 12)

        return ProfileSummary(
            income=finance.income,
            housing=finance.housing,
            credit=finance.credit,
            credit_months=finance.credit_months,
            capital=finance.capital,
            emo_rate=finance.emo_rate,
            smart_base=smart_base,
            emo_spend=emo_spend,
            free_remainder=free_remainder,
            capital_growth_monthly=capital_growth,
        )

    async def delete_account(self, user: User, data: DeleteAccountRequest) -> None:
        if not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")
        await self._repo.update_fields(
            user.id,
            status=UserStatus.PENDING_DELETION,
            deleted_at=datetime.now(UTC),
        )
        await self._session.commit()

    async def cancel_deletion(self, user: User) -> UserResponse:
        if user.status != UserStatus.PENDING_DELETION:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is not pending deletion")
        await self._repo.update_fields(
            user.id,
            status=UserStatus.UNVERIFIED,
            deleted_at=None,
        )
        await self._session.commit()
        refreshed = await self._repo.get_by_id(user.id)
        return _user_to_response(refreshed)

    async def get_public_profile(self, target_id: uuid.UUID, viewer_id: uuid.UUID | None = None) -> UserPublicResponse:
        user = await self._repo.get_by_id(target_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        is_ghost = user.deleted_at is not None
        is_self = viewer_id == target_id if viewer_id else False

        follow_repo = FollowRepository(self._session)
        is_following = False
        if viewer_id and not is_self:
            is_following = await follow_repo.exists(viewer_id, target_id)

        privacy = getattr(user, "privacy_profile", "all")
        is_private = False
        if not is_self and not is_ghost and (privacy == "me" or (privacy == "followers" and not is_following)):
            is_private = True

        followers_count = await follow_repo.count_followers(target_id)
        following_count = await follow_repo.count_following(target_id)

        article_repo = ArticleRepository(self._session)
        articles_count = await article_repo.count_by_author(target_id)

        catalog_repo = CatalogRepository(self._session)
        _, sets_count = await catalog_repo.list_by_author(target_id, limit=0, offset=0)

        if is_private:
            return UserPublicResponse(
                id=user.id,
                display_name=user.display_name,
                username=user.username,
                initials=user.initials,
                color=user.color,
                joined_at=user.joined_at,
                followers_count=followers_count,
                is_following=is_following,
                is_private=True,
            )

        return UserPublicResponse(
            id=user.id,
            display_name="👻 Привидение" if is_ghost else user.display_name,
            username=None if is_ghost else user.username,
            initials="👻" if is_ghost else user.initials,
            color=user.color,
            bio=None if is_ghost else user.bio,
            avatar_url=None if is_ghost else user.avatar_url,
            joined_at=user.joined_at,
            followers_count=followers_count,
            following_count=following_count,
            articles_count=articles_count,
            sets_count=sets_count,
            is_following=is_following,
            is_deleted=is_ghost,
        )

    async def upload_avatar(self, user: User, file: UploadFile) -> UserResponse:
        allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
        if file.content_type not in allowed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type")

        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 5 MB)")

        ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
        ext = ext_map[file.content_type]
        upload_dir = Path("/app/uploads/avatars")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"{user.id}.{ext}"

        async with aiofiles.open(upload_dir / file_name, "wb") as f:
            await f.write(content)

        avatar_url = f"/uploads/avatars/{file_name}"
        await self._repo.update_fields(user.id, avatar_url=avatar_url)
        await self._session.commit()
        refreshed = await self._repo.get_by_id(user.id)
        return _user_to_response(refreshed)

    async def delete_avatar(self, user: User) -> UserResponse:
        if user.avatar_url:
            file_path = Path("/app") / user.avatar_url.lstrip("/")
            if file_path.exists():
                file_path.unlink()
        await self._repo.update_fields(user.id, avatar_url=None)
        await self._session.commit()
        refreshed = await self._repo.get_by_id(user.id)
        return _user_to_response(refreshed)
