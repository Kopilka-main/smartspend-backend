import os
import subprocess
import sys
from collections.abc import AsyncGenerator

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/smartspend_test",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-32-characters-long")

import pytest_asyncio  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.engine.url import make_url  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402

TEST_DATABASE_URL = os.environ["DATABASE_URL"]


async def _ensure_database_exists(url: str) -> None:
    """Create target database if missing (connects to the `postgres` admin DB)."""
    url_obj = make_url(url)
    target_db = url_obj.database
    if not target_db:
        raise RuntimeError(f"DATABASE_URL has no database component: {url}")

    admin_url = url_obj.set(database="postgres")
    engine = create_async_engine(str(admin_url), isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": target_db},
            )
            if not exists:
                await conn.execute(text(f'CREATE DATABASE "{target_db}"'))
    finally:
        await engine.dispose()


async def _reset_public_schema(url: str) -> None:
    """Drop and recreate the public schema so alembic starts from a clean state."""
    engine = create_async_engine(url, isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
    finally:
        await engine.dispose()


def _run_alembic_upgrade() -> None:
    """Apply all migrations to the test database.

    We shell out so that alembic's own asyncio.run() in migrations/env.py does
    not clash with the pytest-asyncio event loop.
    """
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"alembic upgrade failed (exit {result.returncode})\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _prepare_database() -> AsyncGenerator[None, None]:
    await _ensure_database_exists(TEST_DATABASE_URL)
    await _reset_public_schema(TEST_DATABASE_URL)
    _run_alembic_upgrade()
    yield


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator:
    eng = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest_asyncio.fixture()
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Per-test session wrapped in an outer transaction + SAVEPOINT.

    Everything a test does is rolled back at the end, so tests stay isolated
    without TRUNCATE-ing tables. `join_transaction_mode="create_savepoint"`
    lets tests safely call `session.commit()` — it commits only the savepoint.
    """
    async with engine.connect() as connection:
        trans = await connection.begin()
        async_session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield async_session
        finally:
            await async_session.close()
            if trans.is_active:
                await trans.rollback()
