from fastapi import APIRouter, Query

from src.app.core.dependencies import CurrentUser, Session
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
async def list_items(user: CurrentUser, session: Session, group_id: str | None = Query(None)):
    service = InventoryService(session)
    return ApiResponse(data=await service.list_items(user.id, group_id))


@router.get("/items/{item_id}", response_model=ApiResponse[InventoryItemResponse])
async def get_item(item_id: str, user: CurrentUser, session: Session):
    service = InventoryService(session)
    return ApiResponse(data=await service.get_item(item_id, user.id))


@router.post("/items", response_model=ApiResponse[InventoryItemResponse], status_code=201)
async def create_item(body: InventoryItemCreate, user: CurrentUser, session: Session):
    service = InventoryService(session)
    return ApiResponse(data=await service.create_item(user, body))


@router.put("/items/{item_id}", response_model=ApiResponse[InventoryItemResponse])
async def update_item(item_id: str, body: InventoryItemUpdate, user: CurrentUser, session: Session):
    service = InventoryService(session)
    return ApiResponse(data=await service.update_item(item_id, user.id, body))


@router.put("/items/{item_id}/activate", response_model=ApiResponse[InventoryItemResponse])
async def activate_item(item_id: str, body: ActivateItemRequest, user: CurrentUser, session: Session):
    service = InventoryService(session)
    return ApiResponse(data=await service.activate_item(item_id, user.id, body))


@router.post("/items/{item_id}/restock", response_model=ApiResponse[InventoryItemResponse])
async def restock_item(item_id: str, body: RestockRequest, user: CurrentUser, session: Session):
    service = InventoryService(session)
    return ApiResponse(data=await service.restock_item(item_id, user.id, body))


@router.put("/items/{item_id}/replace", response_model=ApiResponse[InventoryItemResponse])
async def replace_item(item_id: str, body: ReplaceRequest, user: CurrentUser, session: Session):
    service = InventoryService(session)
    return ApiResponse(data=await service.replace_item(item_id, user.id, body))


@router.put("/items/{item_id}/set", response_model=ApiResponse[InventoryItemResponse])
async def reassign_set(item_id: str, body: ReassignSetRequest, user: CurrentUser, session: Session):
    service = InventoryService(session)
    return ApiResponse(data=await service.reassign_set(item_id, user.id, body.set_id))


@router.delete("/items/{item_id}", response_model=ApiResponse[None])
async def delete_item(item_id: str, user: CurrentUser, session: Session):
    service = InventoryService(session)
    await service.delete_item(item_id, user.id)
    return ApiResponse(data=None)


@router.post("/items/{item_id}/photos", response_model=ApiResponse[InventoryPhotoResponse], status_code=201)
async def add_photo(item_id: str, user: CurrentUser, session: Session):
    service = InventoryService(session)
    return ApiResponse(data=await service.add_photo(item_id, user.id, url="placeholder", file_name="placeholder"))


@router.delete("/photos/{photo_id}", response_model=ApiResponse[None])
async def delete_photo(photo_id: int, user: CurrentUser, session: Session):
    service = InventoryService(session)
    await service.delete_photo(photo_id, user.id)
    return ApiResponse(data=None)
