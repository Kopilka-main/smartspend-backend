import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.inventory_item import InventoryItem, InventoryPhoto, InventoryPurchase


class InventoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, item_id: str) -> InventoryItem | None:
        stmt = (
            select(InventoryItem)
            .options(
                selectinload(InventoryItem.purchases),
                selectinload(InventoryItem.photos),
            )
            .where(InventoryItem.id == item_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID, group_id: str | None = None) -> list[InventoryItem]:
        stmt = (
            select(InventoryItem)
            .options(
                selectinload(InventoryItem.purchases),
                selectinload(InventoryItem.photos),
            )
            .where(InventoryItem.user_id == user_id)
        )
        if group_id and group_id != "all":
            stmt = stmt.where(InventoryItem.group_id == group_id)
        stmt = stmt.order_by(InventoryItem.group_id, InventoryItem.created_at)
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def create(self, item: InventoryItem) -> InventoryItem:
        self._session.add(item)
        await self._session.flush()
        await self._session.refresh(item)
        return item

    async def bulk_create(self, items: list[InventoryItem]) -> None:
        self._session.add_all(items)
        await self._session.flush()

    async def update_fields(self, item_id: str, **kwargs) -> None:
        stmt = update(InventoryItem).where(InventoryItem.id == item_id).values(**kwargs)
        await self._session.execute(stmt)

    async def delete_item(self, item_id: str) -> None:
        item = await self._session.get(InventoryItem, item_id)
        if item:
            await self._session.delete(item)
            await self._session.flush()

    async def delete_paused_by_set(self, user_id: uuid.UUID, set_id: str) -> int:
        stmt = (
            delete(InventoryItem)
            .where(
                InventoryItem.user_id == user_id,
                InventoryItem.set_id == set_id,
                InventoryItem.paused.is_(True),
            )
            .returning(InventoryItem.id)
        )
        result = await self._session.execute(stmt)
        return len(result.all())

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count()).where(InventoryItem.user_id == user_id)
        return (await self._session.execute(stmt)).scalar_one()

    async def add_purchases(self, purchases: list[InventoryPurchase]) -> None:
        self._session.add_all(purchases)
        await self._session.flush()

    async def update_purchase(self, purchase_id: int, **kwargs) -> None:
        stmt = update(InventoryPurchase).where(InventoryPurchase.id == purchase_id).values(**kwargs)
        await self._session.execute(stmt)

    async def add_photo(self, photo: InventoryPhoto) -> InventoryPhoto:
        self._session.add(photo)
        await self._session.flush()
        await self._session.refresh(photo)
        return photo

    async def get_photo(self, photo_id: int) -> InventoryPhoto | None:
        return await self._session.get(InventoryPhoto, photo_id)

    async def delete_photo(self, photo_id: int) -> None:
        photo = await self._session.get(InventoryPhoto, photo_id)
        if photo:
            await self._session.delete(photo)
            await self._session.flush()
