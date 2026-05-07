import base64
import hashlib
import secrets
import uuid as _uuid
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.security import create_access_token, create_refresh_token
from src.app.models.oauth_state import OAuthState
from src.app.models.user import User
from src.app.models.user_finance import UserFinance
from src.app.models.user_oauth_link import UserOAuthLink
from src.app.schemas.auth import TokenPair


def _build_initials(name: str) -> str:
    parts = name.strip().split()
    return "".join(p[0] for p in parts if p)[:2].upper() or "??"


def _generate_code_verifier() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode("ascii")


def _generate_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _vk_redirect_uri() -> str:
    return f"{settings.frontend_url.rstrip('/')}/api/v1/auth/callback/vk"


def _yandex_redirect_uri() -> str:
    return f"{settings.frontend_url.rstrip('/')}/api/v1/auth/callback/yandex"


async def _save_state(
    session: AsyncSession,
    state: str,
    provider: str,
    verifier: str | None = None,
    link_user_id: str | None = None,
) -> None:
    row = OAuthState(
        state=state,
        provider=provider,
        verifier=verifier,
        link_user_id=_uuid.UUID(link_user_id) if link_user_id else None,
    )
    session.add(row)
    await session.flush()
    cutoff = datetime.now(UTC) - timedelta(hours=1)
    await session.execute(sa_delete(OAuthState).where(OAuthState.created_at < cutoff))
    await session.commit()


async def _pop_state(session: AsyncSession, state: str) -> OAuthState | None:
    if not state:
        return None
    row = await session.get(OAuthState, state)
    if row is None:
        return None
    await session.delete(row)
    await session.flush()
    return row


async def _get_or_create_user(
    session: AsyncSession,
    provider: str,
    oauth_id: str,
    email: str | None,
    display_name: str,
) -> User:
    link_stmt = select(UserOAuthLink).where(UserOAuthLink.provider == provider, UserOAuthLink.oauth_id == oauth_id)
    link = (await session.execute(link_stmt)).scalar_one_or_none()
    if link is not None:
        user = await session.get(User, link.user_id)
        if user is not None:
            return user

    if email:
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is not None:
            await _attach_link(session, user.id, provider, oauth_id)
            return user

    fake_email = email or f"{provider}_{oauth_id}@oauth.smartspend"
    user = User(
        email=fake_email,
        password_hash="oauth",
        display_name=display_name,
        initials=_build_initials(display_name),
        oauth_provider=provider,
        oauth_id=oauth_id,
    )
    session.add(user)
    await session.flush()
    finance = UserFinance(user_id=user.id)
    session.add(finance)
    await _attach_link(session, user.id, provider, oauth_id, is_primary=True)
    await session.flush()
    await session.refresh(user)
    return user


async def _attach_link(
    session: AsyncSession,
    user_id: _uuid.UUID,
    provider: str,
    oauth_id: str,
    is_primary: bool = False,
) -> None:
    existing = await session.execute(
        select(UserOAuthLink).where(UserOAuthLink.user_id == user_id, UserOAuthLink.provider == provider)
    )
    row = existing.scalar_one_or_none()
    if row is not None:
        row.oauth_id = oauth_id
        await session.flush()
        return
    link = UserOAuthLink(user_id=user_id, provider=provider, oauth_id=oauth_id, is_primary=is_primary)
    session.add(link)
    await session.flush()


async def get_yandex_auth_url(session: AsyncSession, link_user_id: str | None = None) -> str:
    state = secrets.token_urlsafe(16)
    await _save_state(session, state, "yandex", link_user_id=link_user_id)
    url = (
        "https://oauth.yandex.ru/authorize"
        "?response_type=code"
        f"&client_id={settings.yandex_client_id}"
        f"&redirect_uri={_yandex_redirect_uri()}"
        f"&state={state}"
    )
    return url


async def get_vk_auth_url(session: AsyncSession, link_user_id: str | None = None) -> tuple[str, str]:
    verifier = _generate_code_verifier()
    state = secrets.token_urlsafe(32)
    await _save_state(session, state, "vk", verifier=verifier, link_user_id=link_user_id)

    challenge = _generate_code_challenge(verifier)
    url = (
        "https://id.vk.ru/authorize"
        "?response_type=code"
        f"&client_id={settings.vk_app_id}"
        f"&redirect_uri={_vk_redirect_uri()}"
        "&scope=email phone"
        f"&state={state}"
        f"&code_challenge={challenge}"
        "&code_challenge_method=s256"
        "&v=2.6.5"
    )
    return url, state


async def handle_yandex_callback(code: str, session: AsyncSession, state: str = "") -> tuple[User, TokenPair]:
    state_row = await _pop_state(session, state)
    link_user_id = str(state_row.link_user_id) if state_row and state_row.link_user_id else None

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth.yandex.ru/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.yandex_client_id,
                "client_secret": settings.yandex_client_secret,
            },
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError(f"Yandex token exchange failed: {token_data}")

        info_resp = await client.get(
            "https://login.yandex.ru/info",
            headers={"Authorization": f"OAuth {access_token}"},
            params={"format": "json"},
        )
        info = info_resp.json()

    yandex_id = str(info["id"])
    email = info.get("default_email")
    name = info.get("display_name") or info.get("real_name") or "Пользователь"

    if link_user_id:
        existing_user = await session.get(User, _uuid.UUID(link_user_id))
        if existing_user is None:
            raise ValueError("User not found for linking")
        await _attach_link(session, existing_user.id, "yandex", yandex_id)
        user = existing_user
        user._was_link = True
    else:
        user = await _get_or_create_user(session, "yandex", yandex_id, email, name)
    await session.commit()

    tokens = TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )
    return user, tokens


async def handle_vk_callback(code: str, device_id: str, state: str, session: AsyncSession) -> tuple[User, TokenPair]:
    state_row = await _pop_state(session, state)
    if state_row is None or state_row.verifier is None:
        raise ValueError("Invalid or expired state")
    verifier = state_row.verifier
    link_user_id = str(state_row.link_user_id) if state_row.link_user_id else None

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://id.vk.ru/oauth2/auth",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.vk_app_id,
                "redirect_uri": _vk_redirect_uri(),
                "device_id": device_id,
                "code_verifier": verifier,
                "state": state,
            },
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError(f"VK token exchange failed: {token_data}")

        info_resp = await client.post(
            "https://id.vk.ru/oauth2/user_info",
            data={
                "client_id": settings.vk_app_id,
                "access_token": access_token,
            },
        )
        info_data = info_resp.json()
        vk_user = info_data.get("user", {})

        vk_id = str(vk_user.get("user_id", ""))
        first = vk_user.get("first_name", "")
        last = vk_user.get("last_name", "")
        email = vk_user.get("email")
        name = f"{first} {last}".strip() or "Пользователь"

    if link_user_id:
        existing_user = await session.get(User, _uuid.UUID(link_user_id))
        if existing_user is None:
            raise ValueError("User not found for linking")
        await _attach_link(session, existing_user.id, "vk", vk_id)
        user = existing_user
        user._was_link = True
    else:
        user = await _get_or_create_user(session, "vk", vk_id, email, name)
    await session.commit()

    tokens = TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )
    return user, tokens
