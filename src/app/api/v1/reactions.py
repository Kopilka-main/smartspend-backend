"""Reaction endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_session
from src.app.core.dependencies import get_current_user
from src.app.models.user import User
from src.app.schemas.base import ApiResponse
from src.app.schemas.reaction import ReactionCreate, ReactionResponse
from src.app.services.reaction import ReactionService

router = APIRouter(prefix="/reactions", tags=["reactions"])


@router.post("", response_model=ApiResponse[ReactionResponse | None])
async def toggle_reaction(
    body: ReactionCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Toggle a like/dislike. Returns reaction if created, null if removed."""
    service = ReactionService(session)
    result = await service.toggle_reaction(user.id, body)
    return ApiResponse(data=result)


@router.get("/my", response_model=ApiResponse[list[ReactionResponse]])
async def get_my_reactions(
    target_type: str | None = Query(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get current user's reactions, optionally filtered by target type."""
    service = ReactionService(session)
    reactions = await service.get_user_reactions(user.id, target_type)
    return ApiResponse(data=reactions)
