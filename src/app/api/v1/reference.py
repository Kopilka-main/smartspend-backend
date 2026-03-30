"""Reference data endpoints (inventory groups, envelope categories)."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_session
from src.app.models.envelope_category import EnvelopeCategory
from src.app.models.inventory_group import InventoryGroup
from src.app.schemas.base import ApiResponse

router = APIRouter(prefix="/reference", tags=["reference"])


@router.get("/envelope-categories", response_model=ApiResponse[list])
async def list_envelope_categories(session: AsyncSession = Depends(get_session)):
    """List all envelope categories."""
    stmt = select(EnvelopeCategory).order_by(EnvelopeCategory.id)
    result = await session.execute(stmt)
    cats = result.scalars().all()
    return ApiResponse(data=[
        {"id": c.id, "name": c.name, "color": c.color} for c in cats
    ])


@router.get("/inventory-groups", response_model=ApiResponse[list])
async def list_inventory_groups(session: AsyncSession = Depends(get_session)):
    """List all inventory groups."""
    stmt = select(InventoryGroup).order_by(InventoryGroup.id)
    result = await session.execute(stmt)
    groups = result.scalars().all()
    return ApiResponse(data=[
        {"id": g.id, "name": g.name, "color": g.color} for g in groups
    ])
