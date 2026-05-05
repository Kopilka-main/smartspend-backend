import base64
import hashlib
import secrets

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.security import create_access_token, create_refresh_token
from src.app.models.user import User
from src.app.models.user_finance import UserFinance
from src.app.schemas.auth import TokenPair

_vk_pkce_store: dict[str, str] = {}


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


async def _get_or_create_user(
    session: AsyncSession,
    provider: str,
    oauth_id: str,
    email: str | None,
    display_name: str,
) -> User:
    stmt = select(User).where(User.oauth_provider == provider, User.oauth_id == oauth_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is not None:
        return user

    if email:
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is not None:
            user.oauth_provider = provider
            user.oauth_id = oauth_id
            await session.flush()
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
    await session.flush()
    await session.refresh(user)
    return user


def get_yandex_auth_url() -> str:
    return (
        "https://oauth.yandex.ru/authorize"
        "?response_type=code"
        f"&client_id={settings.yandex_client_id}"
        f"&redirect_uri={_yandex_redirect_uri()}"
    )


def get_vk_auth_url() -> tuple[str, str]:
    verifier = _generate_code_verifier()
    state = secrets.token_urlsafe(32)
    _vk_pkce_store[state] = verifier
    if len(_vk_pkce_store) > 1000:
        for k in list(_vk_pkce_store.keys())[:500]:
            _vk_pkce_store.pop(k, None)

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


async def handle_yandex_callback(code: str, session: AsyncSession) -> tuple[User, TokenPair]:
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

    user = await _get_or_create_user(session, "yandex", yandex_id, email, name)
    await session.commit()

    tokens = TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )
    return user, tokens


async def handle_vk_callback(code: str, device_id: str, state: str, session: AsyncSession) -> tuple[User, TokenPair]:
    verifier = _vk_pkce_store.pop(state, None)
    if verifier is None:
        raise ValueError("Invalid or expired state")

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

    user = await _get_or_create_user(session, "vk", vk_id, email, name)
    await session.commit()

    tokens = TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )
    return user, tokens
