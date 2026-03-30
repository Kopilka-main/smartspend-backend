from fastapi import APIRouter, Query

from src.app.core.dependencies import CurrentUser, Session
from src.app.schemas.base import ApiResponse
from src.app.schemas.reaction import ReactionCreate, ReactionResponse
from src.app.services.reaction import ReactionService

router = APIRouter(prefix="/reactions", tags=["reactions"])


@router.post("", response_model=ApiResponse[ReactionResponse | None])
async def toggle_reaction(body: ReactionCreate, user: CurrentUser, session: Session):
    service = ReactionService(session)
    result = await service.toggle_reaction(user.id, body)
    return ApiResponse(data=result)


@router.get("/my", response_model=ApiResponse[list[ReactionResponse]])
async def get_my_reactions(user: CurrentUser, session: Session, target_type: str | None = Query(None)):
    service = ReactionService(session)
    return ApiResponse(data=await service.get_user_reactions(user.id, target_type))
