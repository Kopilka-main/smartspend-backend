from fastapi import APIRouter

from src.app.core.dependencies import CurrentUser, Session
from src.app.schemas.base import ApiResponse
from src.app.schemas.envelope import EnvelopeCategoryResponse, EnvelopeResponse
from src.app.services.envelope import EnvelopeService

router = APIRouter(prefix="/envelopes", tags=["envelopes"])


@router.get("/categories", response_model=ApiResponse[list[EnvelopeCategoryResponse]])
async def list_categories(session: Session):
    service = EnvelopeService(session)
    return ApiResponse(data=await service.list_categories())


@router.get("", response_model=ApiResponse[list[EnvelopeResponse]])
async def list_envelopes(user: CurrentUser, session: Session):
    service = EnvelopeService(session)
    return ApiResponse(data=await service.list_envelopes(user.id))


@router.get("/sets/{set_id}", response_model=ApiResponse[EnvelopeResponse | None])
async def get_envelope_by_set(set_id: str, user: CurrentUser, session: Session):
    service = EnvelopeService(session)
    return ApiResponse(data=await service.get_envelope_by_set(user.id, set_id))


@router.post("/sets/{set_id}", response_model=ApiResponse[EnvelopeResponse], status_code=201)
async def add_set_to_profile(set_id: str, user: CurrentUser, session: Session, body: dict | None = None):
    service = EnvelopeService(session)
    scale = None
    items = None
    if body:
        scale = body.get("scale")
        items = body.get("items")
    return ApiResponse(data=await service.add_set_to_profile(user, set_id, scale=scale, items=items))


@router.delete("/sets/{set_id}", response_model=ApiResponse[None])
async def remove_set_from_profile(set_id: str, user: CurrentUser, session: Session):
    service = EnvelopeService(session)
    await service.remove_set_from_profile(user, set_id)
    return ApiResponse(data=None)


@router.delete("/{envelope_id}", response_model=ApiResponse[None])
async def delete_envelope(envelope_id: int, user: CurrentUser, session: Session):
    service = EnvelopeService(session)
    await service.delete_envelope(envelope_id, user.id)
    return ApiResponse(data=None)


@router.put("/sets/{set_id}/pause", response_model=ApiResponse[None])
async def pause_envelope(set_id: str, user: CurrentUser, session: Session):
    service = EnvelopeService(session)
    await service.toggle_pause(user, set_id, paused=True)
    return ApiResponse(data=None)


@router.put("/sets/{set_id}/start", response_model=ApiResponse[None])
async def start_envelope(set_id: str, user: CurrentUser, session: Session):
    service = EnvelopeService(session)
    await service.toggle_pause(user, set_id, paused=False)
    return ApiResponse(data=None)


@router.put("/sets/{set_id}/scale", response_model=ApiResponse[EnvelopeResponse])
async def update_envelope_scale(set_id: str, body: dict, user: CurrentUser, session: Session):
    service = EnvelopeService(session)
    scale = body.get("scale", 1)
    return ApiResponse(data=await service.update_scale(user, set_id, scale))


@router.post("/sets/{set_id}/reset", response_model=ApiResponse[EnvelopeResponse])
async def reset_envelope(set_id: str, user: CurrentUser, session: Session):
    service = EnvelopeService(session)
    return ApiResponse(data=await service.reset_envelope(user, set_id))


@router.put("/sets/{set_id}/items", response_model=ApiResponse[EnvelopeResponse])
async def update_envelope_items(set_id: str, body: dict, user: CurrentUser, session: Session):
    service = EnvelopeService(session)
    return ApiResponse(data=await service.update_items(user, set_id, body.get("items", [])))
