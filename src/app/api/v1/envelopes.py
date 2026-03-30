"""Envelope (budget) endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_session
from src.app.core.dependencies import get_current_user
from src.app.models.user import User
from src.app.schemas.base import ApiResponse
from src.app.schemas.envelope import EnvelopeCategoryResponse, EnvelopeResponse
from src.app.services.envelope import EnvelopeService

router = APIRouter(prefix="/envelopes", tags=["envelopes"])


@router.get("/categories", response_model=ApiResponse[list[EnvelopeCategoryResponse]])
async def list_categories(session: AsyncSession = Depends(get_session)):
    """List all envelope categories (reference data)."""
    service = EnvelopeService(session)
    cats = await service.list_categories()
    return ApiResponse(data=cats)


@router.get("", response_model=ApiResponse[list[EnvelopeResponse]])
async def list_envelopes(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all envelopes for current user."""
    service = EnvelopeService(session)
    envelopes = await service.list_envelopes(user.id)
    return ApiResponse(data=envelopes)


@router.post("/sets/{set_id}", response_model=ApiResponse[EnvelopeResponse], status_code=201)
async def add_set_to_profile(
    set_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add a catalog set to user's profile (creates envelope + frozen inventory items)."""
    service = EnvelopeService(session)
    envelope = await service.add_set_to_profile(user, set_id)
    return ApiResponse(data=envelope)


@router.delete("/sets/{set_id}", response_model=ApiResponse[None])
async def remove_set_from_profile(
    set_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Remove a set from user's profile."""
    service = EnvelopeService(session)
    await service.remove_set_from_profile(user, set_id)
    return ApiResponse(data=None)


@router.delete("/{envelope_id}", response_model=ApiResponse[None])
async def delete_envelope(
    envelope_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete an envelope directly."""
    service = EnvelopeService(session)
    await service.delete_envelope(envelope_id, user.id)
    return ApiResponse(data=None)
