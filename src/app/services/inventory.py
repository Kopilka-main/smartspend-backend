import math
import time
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.inventory_group import InventoryGroup
from src.app.models.inventory_item import InventoryItem, InventoryPhoto, InventoryPurchase
from src.app.models.set import Set
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
MAX_FILE_SIZE = 5 * 1024 * 1024

DAYS_PER_MONTH = Decimal("30.44")

_WEAR_UNIT_TO_DAYS: dict[str, int] = {
    "days": 1,
    "weeks": 7,
    "months": 30,
    "years": 365,
}

_USE_PERIOD_TO_DAYS: dict[str, int] = {
    "day": 1,
    "week": 7,
    "month": 30,
}


def _wear_life_to_weeks(wear_life: int | None, unit: str | None) -> int | None:
    if wear_life is None or unit is None:
        return None
    days_per_unit = _WEAR_UNIT_TO_DAYS.get(unit)
    if days_per_unit is None:
        return None
    total_days = wear_life * days_per_unit
    return max(1, round(total_days / 7))


def _use_rate_to_daily(use_rate: Decimal | None, period: str | None) -> Decimal | None:
    if use_rate is None or period is None:
        return None
    days = _USE_PERIOD_TO_DAYS.get(period)
    if days is None:
        return None
    return use_rate / Decimal(days)


def _weeks_to_wear_life(weeks: int | None) -> tuple[int | None, str | None]:
    if weeks is None:
        return None, None
    return weeks, "weeks"


def _daily_to_use_rate(daily: Decimal | None) -> tuple[Decimal | None, str | None]:
    if daily is None:
        return None, None
    return daily, "day"


def _item_to_response(
    item: InventoryItem,
    group_names: dict[str, str],
    set_names: dict[str, str],
) -> InventoryItemResponse:
    wear_life = item.wear_life
    wear_life_unit = item.wear_life_unit
    if wear_life is None and item.wear_life_weeks is not None:
        wear_life, wear_life_unit = _weeks_to_wear_life(item.wear_life_weeks)

    use_rate = item.use_rate
    use_period = item.use_period
    if use_rate is None and item.daily_use is not None:
        use_rate, use_period = _daily_to_use_rate(item.daily_use)

    daily_use = item.daily_use or Decimal(0)
    qty = item.qty or Decimal(0)
    price = item.price or 0

    remaining_qty: Decimal | None = None
    remaining_percent: int | None = None
    remaining_days: int | None = None
    monthly_cost = 0
    price_per_unit: Decimal | None = None
    item_status = "ok"

    if item.type == "consumable":
        if qty > 0 and daily_use > 0 and item.last_bought is not None:
            days_since = (date.today() - item.last_bought).days
            used = daily_use * Decimal(max(days_since, 0))
            remaining_qty = max(qty - used, Decimal(0))
            if qty > 0:
                remaining_percent = max(0, min(100, int(remaining_qty * 100 / qty)))
            if daily_use > 0:
                remaining_days = int(remaining_qty / daily_use)
        elif qty > 0 and daily_use > 0:
            remaining_qty = qty
            remaining_percent = 100
            remaining_days = int(qty / daily_use)
        else:
            remaining_qty = qty
            remaining_percent = 100 if qty > 0 else 0
            remaining_days = None

        if daily_use > 0 and price > 0 and qty > 0:
            monthly_cost = math.ceil(float(daily_use * DAYS_PER_MONTH * Decimal(price) / qty))

    monthly_need: Decimal | None = None
    if item.type == "consumable" and daily_use > 0:
        monthly_need = round(daily_use * DAYS_PER_MONTH, 2)

    elif item.type == "wear":
        wear_weeks = item.wear_life_weeks
        if wear_weeks is None and wear_life is not None and wear_life_unit is not None:
            wear_weeks = _wear_life_to_weeks(wear_life, wear_life_unit)
        if wear_weeks and wear_weeks > 0 and price > 0:
            wear_days = Decimal(wear_weeks * 7)
            monthly_cost = math.ceil(float(Decimal(price) / wear_days * DAYS_PER_MONTH))

    residual_percent: int | None = None
    residual_value: int | None = None
    if item.type == "wear":
        wear_wk = item.wear_life_weeks
        if wear_wk is None and wear_life is not None and wear_life_unit is not None:
            wear_wk = _wear_life_to_weeks(wear_life, wear_life_unit)
        if item.purchase_date is not None and wear_wk and wear_wk > 0 and price > 0:
            total_days = wear_wk * 7
            used_days = (date.today() - item.purchase_date).days
            pct = max(0, min(100, int((1 - used_days / total_days) * 100)))
            residual_percent = pct
            residual_value = int(price * pct / 100)
            remaining_percent = pct
        elif price > 0:
            residual_percent = 100
            residual_value = price
            remaining_percent = 100

    if qty > 0:
        price_per_unit = Decimal(price) / qty

    if item.paused:
        item_status = "paused"
    elif item.type == "consumable":
        if (remaining_days is not None and remaining_days <= 0) or qty == 0 or item.qty is None:
            item_status = "urgent"
        elif remaining_days is not None and remaining_days <= 7:
            item_status = "soon"
    return InventoryItemResponse(
        id=item.id,
        user_id=str(item.user_id),
        group_id=item.group_id,
        group_name=group_names.get(item.group_id),
        type=item.type,
        name=item.name,
        price=price,
        set_id=item.set_id,
        set_name=set_names.get(item.set_id) if item.set_id else None,
        is_extra=item.is_extra,
        paused=item.paused,
        notes=item.notes,
        qty=item.qty,
        unit=item.unit,
        daily_use=item.daily_use,
        last_bought=item.last_bought,
        wear_life_weeks=item.wear_life_weeks,
        wear_life=wear_life,
        wear_life_unit=wear_life_unit,
        use_rate=use_rate,
        use_period=use_period,
        purchase_date=item.purchase_date,
        status=item_status,
        remaining_qty=remaining_qty,
        remaining_percent=remaining_percent,
        remaining_days=remaining_days,
        monthly_cost=monthly_cost,
        weekly_cost=math.ceil(monthly_cost / 4.33) if monthly_cost > 0 else 0,
        monthly_need=monthly_need,
        price_per_unit=price_per_unit,
        residual_percent=residual_percent,
        residual_value=residual_value,
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

    async def _get_group_names(self) -> dict[str, str]:
        result = await self._session.execute(select(InventoryGroup.id, InventoryGroup.name))
        return dict(result.all())

    async def _get_set_names(self, set_ids: set[str]) -> dict[str, str]:
        if not set_ids:
            return {}
        result = await self._session.execute(select(Set.id, Set.title).where(Set.id.in_(set_ids)))
        return dict(result.all())

    async def _build_responses(self, items: list[InventoryItem]) -> list[InventoryItemResponse]:
        gn = await self._get_group_names()
        set_ids = {i.set_id for i in items if i.set_id}
        sn = await self._get_set_names(set_ids)
        return [_item_to_response(i, gn, sn) for i in items]

    async def _build_response(self, item: InventoryItem) -> InventoryItemResponse:
        gn = await self._get_group_names()
        sn = await self._get_set_names({item.set_id} if item.set_id else set())
        return _item_to_response(item, gn, sn)

    async def list_items(self, user_id: uuid.UUID, group_id: str | None = None) -> list[InventoryItemResponse]:
        items = await self._repo.list_by_user(user_id, group_id)
        return await self._build_responses(items)

    async def get_item(self, item_id: str, user_id: uuid.UUID) -> InventoryItemResponse:
        item = await self._repo.get_by_id(item_id)
        if item is None or item.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        return await self._build_response(item)

    async def create_item(self, user: User, data: InventoryItemCreate) -> InventoryItemResponse:
        item_id = f"inv_{int(time.time() * 1000)}"

        wear_life_weeks = data.wear_life_weeks
        daily_use = data.daily_use

        if data.wear_life is not None and data.wear_life_unit is not None and wear_life_weeks is None:
            wear_life_weeks = _wear_life_to_weeks(data.wear_life, data.wear_life_unit)

        if data.use_rate is not None and data.use_period is not None and daily_use is None:
            daily_use = _use_rate_to_daily(data.use_rate, data.use_period)

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
            daily_use=daily_use,
            last_bought=data.last_bought,
            wear_life_weeks=wear_life_weeks,
            wear_life=data.wear_life,
            wear_life_unit=data.wear_life_unit,
            use_rate=data.use_rate,
            use_period=data.use_period,
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

        wl = updates.get("wear_life", item.wear_life)
        wlu = updates.get("wear_life_unit", item.wear_life_unit)
        if wl is not None and wlu is not None:
            updates["wear_life_weeks"] = _wear_life_to_weeks(wl, wlu)

        ur = updates.get("use_rate", item.use_rate)
        up = updates.get("use_period", item.use_period)
        if ur is not None and up is not None:
            updates["daily_use"] = _use_rate_to_daily(ur, up)

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
        act_date = data.purchase_date or date.today()
        if item.type == "consumable":
            updates["last_bought"] = act_date
            if data.qty is not None:
                updates["qty"] = data.qty
            if data.price is not None:
                updates["price"] = data.price
        elif item.type == "wear":
            updates["purchase_date"] = act_date
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
