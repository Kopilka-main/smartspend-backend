import time
import uuid
from decimal import Decimal
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.inventory_item import InventoryItem, InventoryPhoto, InventoryPurchase
from src.app.models.user import User
from src.app.repositories.inventory import InventoryRepository
from src.app.schemas.inventory import (
    ActivateItemRequest,
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
    InventoryPhotoResponse,
    InventoryPurchaseResponse,
    ReplaceRequest,
    RestockRequest,
)

UPLOAD_DIR = Path("/app/uploads/photos")
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def _item_to_response(item: InventoryItem) -> InventoryItemResponse:
    return InventoryItemResponse(
        id=item.id,
        user_id=str(item.user_id),
        group_id=item.group_id,
        type=item.type,
        name=item.name,
        price=item.price,
        set_id=item.set_id,
        is_extra=item.is_extra,
        paused=item.paused,
        notes=item.notes,
        qty=item.qty,
        unit=item.unit,
        daily_use=item.daily_use,
        last_bought=item.last_bought,
        wear_life_weeks=item.wear_life_weeks,
        purchase_date=item.purchase_date,
        purchases=[
            InventoryPurchaseResponse(
                id=p.id,
                position=p.position,
                bought=p.bought,
                purchase_date=p.purchase_date,
            )
            for p in (item.purchases or [])
        ],
        photos=[
            InventoryPhotoResponse(
                id=ph.id,
                url=ph.url,
                file_name=ph.file_name,
                created_at=ph.created_at,
            )
            for ph in (item.photos or [])
        ],
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


class InventoryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InventoryRepository(session)

    async def list_items(self, user_id: uuid.UUID, group_id: str | None = None) -> list[InventoryItemResponse]:
        items = await self._repo.list_by_user(user_id, group_id)
        return [_item_to_response(i) for i in items]

    async def get_item(self, item_id: str, user_id: uuid.UUID) -> InventoryItemResponse:
        item = await self._repo.get_by_id(item_id)
        if item is None or item.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        return _item_to_response(item)

    async def create_item(self, user: User, data: InventoryItemCreate) -> InventoryItemResponse:
        item_id = f"inv_{int(time.time() * 1000)}"
        item = InventoryItem(
            id=item_id,
            user_id=user.id,
            group_id=data.group_id,
            type=data.type,
            name=data.name,
            price=data.price,
            set_id=data.set_id,
            is_extra=False,
            paused=False,
            notes=data.notes,
            qty=data.qty,
            unit=data.unit,
            daily_use=data.daily_use,
            last_bought=data.last_bought,
            wear_life_weeks=data.wear_life_weeks,
            purchase_date=data.purchase_date,
        )
        item = await self._repo.create(item)

        if data.type == "wear" and data.qty and data.qty > 1:
            qty_int = int(data.qty)
            purchases = [
                InventoryPurchase(
                    item_id=item_id,
                    position=i,
                    bought=data.purchase_date is not None,
                    purchase_date=data.purchase_date,
                )
                for i in range(qty_int)
            ]
            await self._repo.add_purchases(purchases)

        await self._session.commit()
        return await self.get_item(item_id, user.id)

    async def update_item(self, item_id: str, user_id: uuid.UUID, data: InventoryItemUpdate) -> InventoryItemResponse:
        item = await self._repo.get_by_id(item_id)
        if item is None or item.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        updates = data.model_dump(exclude_unset=True)
        if updates:
            await self._repo.update_fields(item_id, **updates)
            await self._session.commit()
        return await self.get_item(item_id, user_id)

    async def activate_item(self, item_id: str, user_id: uuid.UUID, data: ActivateItemRequest) -> InventoryItemResponse:
        item = await self._repo.get_by_id(item_id)
        if item is None or item.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        if not item.paused:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item is not frozen/paused")

        updates: dict = {"paused": False}
        if item.type == "consumable":
            updates["last_bought"] = data.purchase_date
            if data.qty is not None:
                updates["qty"] = data.qty
            if data.price is not None:
                updates["price"] = data.price
        elif item.type == "wear":
            updates["purchase_date"] = data.purchase_date
            if data.price is not None:
                updates["price"] = data.price

        await self._repo.update_fields(item_id, **updates)
        await self._session.commit()
        return await self.get_item(item_id, user_id)

    async def restock_item(self, item_id: str, user_id: uuid.UUID, data: RestockRequest) -> InventoryItemResponse:
        item = await self._repo.get_by_id(item_id)
        if item is None or item.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        if item.type != "consumable":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only consumables can be restocked")

        new_qty = (item.qty or Decimal("0")) + data.qty_added
        await self._repo.update_fields(item_id, qty=new_qty)
        await self._session.commit()
        return await self.get_item(item_id, user_id)

    async def replace_item(self, item_id: str, user_id: uuid.UUID, data: ReplaceRequest) -> InventoryItemResponse:
        item = await self._repo.get_by_id(item_id)
        if item is None or item.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        if item.type != "wear":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only wear items can be replaced")

        await self._repo.update_fields(item_id, purchase_date=data.purchase_date)
        await self._session.commit()
        return await self.get_item(item_id, user_id)

    async def reassign_set(self, item_id: str, user_id: uuid.UUID, new_set_id: str) -> InventoryItemResponse:
        item = await self._repo.get_by_id(item_id)
        if item is None or item.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        await self._repo.update_fields(item_id, set_id=new_set_id)
        await self._session.commit()
        return await self.get_item(item_id, user_id)

    async def delete_item(self, item_id: str, user_id: uuid.UUID) -> None:
        item = await self._repo.get_by_id(item_id)
        if item is None or item.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        await self._repo.delete_item(item_id)
        await self._session.commit()

    async def add_photo(self, item_id: str, user_id: uuid.UUID, file: UploadFile) -> InventoryPhotoResponse:
        item = await self._repo.get_by_id(item_id)
        if item is None or item.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type")

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 5 MB)")

        ext = Path(file.filename or "photo.jpg").suffix or ".jpg"
        unique_name = f"{item_id}_{int(time.time() * 1000)}{ext}"
        item_dir = UPLOAD_DIR / item_id
        item_dir.mkdir(parents=True, exist_ok=True)
        file_path = item_dir / unique_name

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        url = f"/uploads/photos/{item_id}/{unique_name}"
        photo = InventoryPhoto(item_id=item_id, url=url, file_name=file.filename or unique_name)
        photo = await self._repo.add_photo(photo)
        await self._session.commit()
        return InventoryPhotoResponse(
            id=photo.id,
            url=photo.url,
            file_name=photo.file_name,
            created_at=photo.created_at,
        )

    async def delete_photo(self, photo_id: int, user_id: uuid.UUID) -> None:
        photo = await self._repo.get_photo(photo_id)
        if photo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
        item = await self._repo.get_by_id(photo.item_id)
        if item is None or item.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your item")

        file_path = Path("/app") / photo.url.lstrip("/")
        if file_path.exists():
            file_path.unlink()

        await self._repo.delete_photo(photo_id)
        await self._session.commit()
