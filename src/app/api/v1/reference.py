from fastapi import APIRouter
from sqlalchemy import select

from src.app.core.dependencies import Session
from src.app.models.envelope_category import EnvelopeCategory
from src.app.models.inventory_group import InventoryGroup
from src.app.schemas.base import ApiResponse

router = APIRouter(prefix="/reference", tags=["reference"])


@router.get("/envelope-categories", response_model=ApiResponse[list])
async def list_envelope_categories(session: Session):
    stmt = select(EnvelopeCategory).order_by(EnvelopeCategory.id)
    result = await session.execute(stmt)
    cats = result.scalars().all()
    return ApiResponse(data=[
        {"id": c.id, "name": c.name, "color": c.color} for c in cats
    ])


@router.get("/inventory-groups", response_model=ApiResponse[list])
async def list_inventory_groups(session: Session):
    stmt = select(InventoryGroup).order_by(InventoryGroup.id)
    result = await session.execute(stmt)
    groups = result.scalars().all()
    return ApiResponse(data=[
        {"id": g.id, "name": g.name, "color": g.color} for g in groups
    ])
