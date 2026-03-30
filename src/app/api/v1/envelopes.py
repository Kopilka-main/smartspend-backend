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


@router.post("/sets/{set_id}", response_model=ApiResponse[EnvelopeResponse], status_code=201)
async def add_set_to_profile(set_id: str, user: CurrentUser, session: Session):
    service = EnvelopeService(session)
    return ApiResponse(data=await service.add_set_to_profile(user, set_id))


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
