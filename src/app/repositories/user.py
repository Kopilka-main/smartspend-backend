import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.user import User
from src.app.models.user_finance import UserFinance


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
    async def get_by_username(self, username: str) -> User | None:
        """Find user by username."""
        stmt = select(User).where(User.username == username)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user: User, finance: UserFinance) -> User:
        self._session.add(user)
        await self._session.flush()
        finance.user_id = user.id
        self._session.add(finance)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def update_fields(self, user_id: uuid.UUID, **kwargs) -> None:
        stmt = update(User).where(User.id == user_id).values(**kwargs)
        await self._session.execute(stmt)

    async def update_finance(self, user_id: uuid.UUID, **kwargs) -> None:
        stmt = update(UserFinance).where(UserFinance.user_id == user_id).values(**kwargs)
        await self._session.execute(stmt)

    async def get_finance(self, user_id: uuid.UUID) -> UserFinance | None:
        return await self._session.get(UserFinance, user_id)
