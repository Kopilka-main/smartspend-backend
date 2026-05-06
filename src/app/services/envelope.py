import time
import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.envelope import Envelope
from src.app.models.inventory_group import InventoryGroupCategory
from src.app.models.inventory_item import InventoryItem
from src.app.models.set import Set
from src.app.models.user import User
from src.app.repositories.catalog import CatalogRepository
from src.app.repositories.envelope import EnvelopeRepository
from src.app.repositories.inventory import InventoryRepository
from src.app.schemas.envelope import EnvelopeCategoryResponse, EnvelopeResponse


class EnvelopeService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = EnvelopeRepository(session)

    async def list_categories(self) -> list[EnvelopeCategoryResponse]:
        cats = await self._repo.list_categories()
        return [EnvelopeCategoryResponse.model_validate(c) for c in cats]

    async def list_envelopes(self, user_id: uuid.UUID) -> list[EnvelopeResponse]:
        rows = await self._repo.list_by_user(user_id)
        result = []
        for e, source in rows:
            paused = await self._check_all_paused(user_id, e.set_id)
            result.append(EnvelopeResponse.from_orm_obj(e, source=source, paused=paused))
        return result

    async def get_envelope_by_set(self, user_id: uuid.UUID, set_id: str) -> EnvelopeResponse | None:
        envelope = await self._repo.find_by_user_set(user_id, set_id)
        if envelope is None:
            return None
        catalog_repo = CatalogRepository(self._session)
        s = await catalog_repo.get_by_id(set_id)
        paused = await self._check_all_paused(user_id, set_id)
        return EnvelopeResponse.from_orm_obj(envelope, source=s.source if s else None, paused=paused)

    async def add_set_to_profile(
        self,
        user: User,
        set_id: str,
        scale: float | str | None = None,
        items: list[dict] | None = None,
    ) -> EnvelopeResponse:
        existing = await self._repo.find_by_user_set(user.id, set_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Set already added to profile",
            )

        catalog_repo = CatalogRepository(self._session)
        s = await catalog_repo.get_by_id(set_id)
        if s is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Set not found",
            )

        total_amount = 0
        for item in s.items or []:
            bp = item.base_price or 0
            qty = item.qty or 1
            py = item.period_years or 0
            if py > 0:
                monthly = int((bp * qty) / (py * 12))
                total_amount += monthly

        env_scale = Decimal(str(scale)) if scale else Decimal("1.00")
        envelope = Envelope(
            user_id=user.id,
            category_id=s.category_id,
            set_id=set_id,
            name=s.title,
            items_count=len(s.items or []),
            amount=total_amount,
            envelope_type="consumable",
            scale=env_scale,
        )
        envelope = await self._repo.create(envelope)

        group_id = await self._resolve_group(s.category_id)
        inv_repo = InventoryRepository(self._session)
        ts = int(time.time() * 1000)

        inv_items = []
        if items:
            for idx, it in enumerate(items):
                item_type = it.get("itemType") or it.get("type") or "consumable"
                wl_weeks = it.get("wearLifeWeeks")
                if wl_weeks is None and it.get("periodYears"):
                    wl_weeks = int(float(it["periodYears"]) * 52)
                inv_items.append(
                    InventoryItem(
                        id=f"inv_{set_id}_{idx}_{ts}",
                        user_id=user.id,
                        group_id=group_id,
                        type=item_type,
                        name=it.get("name", ""),
                        price=int(it.get("price", 0) or 0),
                        set_id=set_id,
                        is_extra=True,
                        paused=True,
                        qty=it.get("qty") if item_type == "consumable" else None,
                        unit=it.get("unit") if item_type == "consumable" else None,
                        daily_use=it.get("dailyUse"),
                        last_bought=None,
                        wear_life_weeks=wl_weeks if item_type == "wear" else None,
                    )
                )
        else:
            for idx, si in enumerate(s.items or []):
                item_id = f"inv_{set_id}_{idx}_{ts}"
                bp = int(si.base_price) if si.base_price else (si.price or 0)
                py = si.period_years or 0
                inv_item = InventoryItem(
                    id=item_id,
                    user_id=user.id,
                    group_id=group_id,
                    type=si.item_type,
                    name=si.name,
                    price=bp,
                    set_id=set_id,
                    is_extra=True,
                    paused=True,
                    qty=si.qty if si.item_type == "consumable" else None,
                    unit=si.unit if si.item_type == "consumable" else None,
                    daily_use=None,
                    last_bought=None,
                    wear_life_weeks=int(py * 52) if si.item_type == "wear" and py > 0 else None,
                )
                inv_items.append(inv_item)

        if inv_items:
            await inv_repo.bulk_create(inv_items)

        stmt = sa_update(Set).where(Set.id == set_id).values(users_count=Set.users_count + 1)
        await self._session.execute(stmt)
        await self._session.commit()
        paused = await self._check_all_paused(user.id, set_id)
        return EnvelopeResponse.from_orm_obj(envelope, source=s.source, paused=paused)

    async def remove_set_from_profile(self, user: User, set_id: str) -> None:
        envelope = await self._repo.find_by_user_set(user.id, set_id)
        if envelope is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Set not in your profile",
            )

        inv_repo = InventoryRepository(self._session)
        await inv_repo.delete_paused_by_set(user.id, set_id)

        await self._repo.delete_by_user_set(user.id, set_id)

        stmt = sa_update(Set).where(Set.id == set_id).values(users_count=func.greatest(0, Set.users_count - 1))
        await self._session.execute(stmt)
        await self._session.commit()

    async def delete_envelope(self, envelope_id: int, user_id: uuid.UUID) -> None:
        envelope = await self._repo.get_by_id(envelope_id)
        if envelope is None or envelope.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Envelope not found",
            )
        await self._repo.delete_envelope(envelope_id)
        await self._session.commit()

    async def _resolve_group(self, category_id: str) -> str:
        stmt = select(InventoryGroupCategory.group_id).where(InventoryGroupCategory.category_id == category_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return row if row else "g8"

    async def _check_all_paused(self, user_id: uuid.UUID, set_id: str) -> bool:
        stmt = select(InventoryItem.paused).where(InventoryItem.user_id == user_id, InventoryItem.set_id == set_id)
        result = await self._session.execute(stmt)
        statuses = result.scalars().all()
        if not statuses:
            return True
        return all(statuses)

    async def toggle_pause(self, user: User, set_id: str, paused: bool) -> None:
        envelope = await self._repo.find_by_user_set(user.id, set_id)
        if envelope is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Set not in your profile",
            )
        stmt = (
            sa_update(InventoryItem)
            .where(InventoryItem.user_id == user.id, InventoryItem.set_id == set_id)
            .values(paused=paused)
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def update_scale(self, user: User, set_id: str, scale) -> EnvelopeResponse:
        envelope = await self._repo.find_by_user_set(user.id, set_id)
        new_scale = Decimal(str(scale))
        if new_scale <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Scale must be > 0")
        if envelope is None:
            return await self.add_set_to_profile(user, set_id, scale=new_scale)
        await self._session.execute(sa_update(Envelope).where(Envelope.id == envelope.id).values(scale=new_scale))
        await self._session.commit()
        await self._session.refresh(envelope)
        paused = await self._check_all_paused(user.id, set_id)
        catalog_repo = CatalogRepository(self._session)
        s = await catalog_repo.get_by_id(set_id)
        return EnvelopeResponse.from_orm_obj(envelope, source=s.source if s else None, paused=paused)

    async def reset_envelope(self, user: User, set_id: str) -> EnvelopeResponse:
        envelope = await self._repo.find_by_user_set(user.id, set_id)
        if envelope is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Set not in your profile",
            )
        catalog_repo = CatalogRepository(self._session)
        s = await catalog_repo.get_by_id(set_id)
        if s is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")

        inv_repo = InventoryRepository(self._session)
        await inv_repo.delete_by_set_and_user(user.id, set_id)

        group_id = await self._resolve_group(s.category_id)
        ts = int(time.time() * 1000)
        inv_items = []
        for idx, si in enumerate(s.items or []):
            item_id = f"inv_{set_id}_{idx}_{ts}"
            bp = int(si.base_price) if si.base_price else (si.price or 0)
            py = si.period_years or 0
            inv_item = InventoryItem(
                id=item_id,
                user_id=user.id,
                group_id=group_id,
                type=si.item_type,
                name=si.name,
                price=bp,
                set_id=set_id,
                is_extra=True,
                paused=True,
                qty=si.qty if si.item_type == "consumable" else None,
                unit=si.unit if si.item_type == "consumable" else None,
                daily_use=None,
                last_bought=None,
                wear_life_weeks=int(py * 52) if si.item_type == "wear" and py > 0 else None,
            )
            inv_items.append(inv_item)
        if inv_items:
            await inv_repo.bulk_create(inv_items)

        await self._session.execute(sa_update(Envelope).where(Envelope.id == envelope.id).values(scale=Decimal("1.00")))
        await self._session.commit()
        await self._session.refresh(envelope)
        paused = await self._check_all_paused(user.id, set_id)
        return EnvelopeResponse.from_orm_obj(envelope, source=s.source, paused=paused)

    async def update_items(self, user: User, set_id: str, items: list[dict]) -> EnvelopeResponse:
        envelope = await self._repo.find_by_user_set(user.id, set_id)
        if envelope is None:
            return await self.add_set_to_profile(user, set_id, items=items)
        catalog_repo = CatalogRepository(self._session)
        s = await catalog_repo.get_by_id(set_id)
        if s is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")

        inv_repo = InventoryRepository(self._session)
        await inv_repo.delete_by_set_and_user(user.id, set_id)

        group_id = await self._resolve_group(s.category_id)
        ts = int(time.time() * 1000)
        inv_items: list[InventoryItem] = []
        for idx, it in enumerate(items):
            item_type = it.get("itemType") or it.get("type") or "consumable"
            wl_weeks = it.get("wearLifeWeeks")
            if wl_weeks is None and it.get("periodYears"):
                wl_weeks = int(float(it["periodYears"]) * 52)
            inv_item = InventoryItem(
                id=f"inv_{set_id}_{idx}_{ts}",
                user_id=user.id,
                group_id=group_id,
                type=item_type,
                name=it.get("name", ""),
                price=int(it.get("price", 0) or 0),
                set_id=set_id,
                is_extra=True,
                paused=True,
                qty=it.get("qty") if item_type == "consumable" else None,
                unit=it.get("unit") if item_type == "consumable" else None,
                daily_use=it.get("dailyUse"),
                last_bought=None,
                wear_life_weeks=wl_weeks if item_type == "wear" else None,
            )
            inv_items.append(inv_item)
        if inv_items:
            await inv_repo.bulk_create(inv_items)

        await self._session.execute(
            sa_update(Envelope).where(Envelope.id == envelope.id).values(items_count=len(inv_items))
        )
        await self._session.commit()
        await self._session.refresh(envelope)
        paused = await self._check_all_paused(user.id, set_id)
        return EnvelopeResponse.from_orm_obj(envelope, source=s.source, paused=paused)
