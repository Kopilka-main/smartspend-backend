"""Inventory endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_session
from src.app.core.dependencies import get_current_user
from src.app.models.user import User
from src.app.schemas.base import ApiResponse
from src.app.schemas.inventory import (
    ActivateItemRequest,
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
    InventoryPhotoResponse,
    ReassignSetRequest,
    ReplaceRequest,
    RestockRequest,
)
from src.app.services.inventory import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/items", response_model=ApiResponse[list[InventoryItemResponse]])
async def list_items(
    group_id: str | None = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all inventory items for current user."""
    service = InventoryService(session)
    items = await service.list_items(user.id, group_id)
    return ApiResponse(data=items)


@router.get("/items/{item_id}", response_model=ApiResponse[InventoryItemResponse])
async def get_item(
    item_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a single inventory item."""
    service = InventoryService(session)
    item = await service.get_item(item_id, user.id)
    return ApiResponse(data=item)


@router.post("/items", response_model=ApiResponse[InventoryItemResponse], status_code=201)
async def create_item(
    body: InventoryItemCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new inventory item manually."""
    service = InventoryService(session)
    item = await service.create_item(user, body)
    return ApiResponse(data=item)


@router.put("/items/{item_id}", response_model=ApiResponse[InventoryItemResponse])
async def update_item(
    item_id: str,
    body: InventoryItemUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update an inventory item."""
    service = InventoryService(session)
    item = await service.update_item(item_id, user.id, body)
    return ApiResponse(data=item)


@router.put("/items/{item_id}/activate", response_model=ApiResponse[InventoryItemResponse])
async def activate_item(
    item_id: str,
    body: ActivateItemRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Activate a frozen item."""
    service = InventoryService(session)
    item = await service.activate_item(item_id, user.id, body)
    return ApiResponse(data=item)


@router.post("/items/{item_id}/restock", response_model=ApiResponse[InventoryItemResponse])
async def restock_item(
    item_id: str,
    body: RestockRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Restock a consumable item."""
    service = InventoryService(session)
    item = await service.restock_item(item_id, user.id, body)
    return ApiResponse(data=item)


@router.put("/items/{item_id}/replace", response_model=ApiResponse[InventoryItemResponse])
async def replace_item(
    item_id: str,
    body: ReplaceRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Replace a wear item (reset wear timer)."""
    service = InventoryService(session)
    item = await service.replace_item(item_id, user.id, body)
    return ApiResponse(data=item)


@router.put("/items/{item_id}/set", response_model=ApiResponse[InventoryItemResponse])
async def reassign_set(
    item_id: str,
    body: ReassignSetRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Reassign an inventory item to a different set."""
    service = InventoryService(session)
    item = await service.reassign_set(item_id, user.id, body.set_id)
    return ApiResponse(data=item)


@router.delete("/items/{item_id}", response_model=ApiResponse[None])
async def delete_item(
    item_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete an inventory item."""
    service = InventoryService(session)
    await service.delete_item(item_id, user.id)
    return ApiResponse(data=None)


# --- photos ---


@router.post(
    "/items/{item_id}/photos",
    response_model=ApiResponse[InventoryPhotoResponse],
    status_code=201,
)
async def add_photo(
    item_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add a photo to an inventory item (placeholder — needs file upload integration)."""
    # TODO: integrate with S3 file upload
    service = InventoryService(session)
    photo = await service.add_photo(item_id, user.id, url="placeholder", file_name="placeholder")
    return ApiResponse(data=photo)


@router.delete("/photos/{photo_id}", response_model=ApiResponse[None])
async def delete_photo(
    photo_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a photo from an inventory item."""
    service = InventoryService(session)
    await service.delete_photo(photo_id, user.id)
    return ApiResponse(data=None)
