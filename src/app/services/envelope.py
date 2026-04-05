import time
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.envelope import Envelope
from src.app.models.inventory_item import InventoryItem
from src.app.models.inventory_group import InventoryGroupCategory
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
        envelopes = await self._repo.list_by_user(user_id)
        return [EnvelopeResponse.from_orm_obj(e) for e in envelopes]

    async def add_set_to_profile(self, user: User, set_id: str) -> EnvelopeResponse:
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
                status_code=status.HTTP_404_NOT_FOUND, detail="Set not found",
            )

        total_amount = 0
        for item in (s.items or []):
            bp = item.base_price or 0
            qty = item.qty or 1
            py = item.period_years or 0
            if py > 0:
                monthly = int((bp * qty) / (py * 12))
                total_amount += monthly

        envelope = Envelope(
            user_id=user.id, category_id=s.category_id, set_id=set_id,
            name=s.title, items_count=len(s.items or []),
            amount=total_amount, envelope_type="consumable",
        )
        envelope = await self._repo.create(envelope)

        group_id = await self._resolve_group(s.category_id)
        inv_repo = InventoryRepository(self._session)
        ts = int(time.time() * 1000)

        inv_items = []
        for idx, si in enumerate(s.items or []):
            item_id = f"inv_{set_id}_{idx}_{ts}"
            bp = int(si.base_price) if si.base_price else (si.price or 0)
            py = si.period_years or 0
            inv_item = InventoryItem(
                id=item_id, user_id=user.id, group_id=group_id,
                type=si.item_type, name=si.name,
                price=bp, set_id=set_id,
                is_extra=True, paused=True,
                qty=si.qty if si.item_type == "consumable" else None,
                unit=si.unit if si.item_type == "consumable" else None,
                daily_use=None, last_bought=None,
                wear_life_weeks=int(py * 52) if si.item_type == "wear" and py > 0 else None,
            )
            inv_items.append(inv_item)

        if inv_items:
            await inv_repo.bulk_create(inv_items)

        stmt = sa_update(Set).where(Set.id == set_id).values(
            users_count=Set.users_count + 1
        )
        await self._session.execute(stmt)
        await self._session.commit()
        return EnvelopeResponse.from_orm_obj(envelope)

    async def remove_set_from_profile(self, user: User, set_id: str) -> None:
        envelope = await self._repo.find_by_user_set(user.id, set_id)
        if envelope is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Set not in your profile",
            )

        inv_repo = InventoryRepository(self._session)
        items = await inv_repo.list_by_user(user.id)
        set_items = [i for i in items if i.set_id == set_id]

        for item in set_items:
            if item.paused:
                await inv_repo.delete_item(item.id)
            else:
                await inv_repo.update_fields(item.id, paused=True)

        await self._repo.delete_by_user_set(user.id, set_id)

        stmt = sa_update(Set).where(Set.id == set_id).values(
            users_count=Set.users_count - 1
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def delete_envelope(self, envelope_id: int, user_id: uuid.UUID) -> None:
        envelope = await self._repo.get_by_id(envelope_id)
        if envelope is None or envelope.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Envelope not found",
            )
        await self._repo.delete_envelope(envelope_id)
        await self._session.commit()

    async def _resolve_group(self, category_id: str) -> str:
        stmt = select(InventoryGroupCategory.group_id).where(
            InventoryGroupCategory.category_id == category_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return row if row else "g8"
