import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.user import User


def _make_user(**overrides) -> User:
    defaults = {
        "email": f"{uuid.uuid4().hex[:12]}@example.com",
        "password_hash": "not-a-real-hash",
        "display_name": "Test User",
        "initials": "TU",
    }
    defaults.update(overrides)
    return User(**defaults)


async def test_user_insert_populates_uuid_and_server_defaults(session: AsyncSession) -> None:
    user = _make_user()
    session.add(user)
    await session.flush()
    await session.refresh(user)

    assert isinstance(user.id, uuid.UUID)
    assert user.created_at is not None
    assert user.joined_at is not None
    assert user.created_at.tzinfo is not None, "Postgres must return tz-aware timestamps"
    assert user.color == "#7DAF92"
    assert user.status == "unverified"


async def test_user_email_is_unique(session: AsyncSession) -> None:
    email = f"dup-{uuid.uuid4().hex[:8]}@example.com"
    session.add(_make_user(email=email))
    await session.flush()

    session.add(_make_user(email=email, display_name="Dup"))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_user_query_by_email(session: AsyncSession) -> None:
    email = f"find-{uuid.uuid4().hex[:8]}@example.com"
    session.add(_make_user(email=email, display_name="Findable"))
    await session.flush()

    result = await session.execute(select(User).where(User.email == email))
    fetched = result.scalar_one()

    assert fetched.email == email
    assert fetched.display_name == "Findable"
    assert isinstance(fetched.id, uuid.UUID)
