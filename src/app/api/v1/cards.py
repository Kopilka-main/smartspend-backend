from fastapi import APIRouter, Query

from src.app.core.dependencies import CurrentUser, Session
from src.app.schemas.base import ApiResponse, PaginationMeta
from src.app.schemas.card import (
    CardCalculateRequest,
    CardCalculateResponse,
    CardResponse,
    UserCardCreate,
    UserCardResponse,
)
from src.app.services.card import CardService

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("", response_model=ApiResponse[list[CardResponse]])
async def list_cards(
    session: Session,
    card_type: str | None = Query(None, alias="cardType"),
    bank_name: str | None = Query(None, alias="bankName"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    service = CardService(session)
    items, total = await service.list_cards(
        card_type=card_type,
        bank_name=bank_name,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        data=items,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.get("/user-cards", response_model=ApiResponse[list[UserCardResponse]])
async def list_user_cards(user: CurrentUser, session: Session):
    service = CardService(session)
    return ApiResponse(data=await service.list_user_cards(user.id))


@router.post("/calculate", response_model=ApiResponse[list[CardCalculateResponse]])
async def calculate_cards(body: CardCalculateRequest, session: Session):
    service = CardService(session)
    return ApiResponse(data=await service.calculate(body.spending))


@router.get("/{card_id}", response_model=ApiResponse[CardResponse])
async def get_card(card_id: str, session: Session):
    service = CardService(session)
    return ApiResponse(data=await service.get_card(card_id))


@router.post("/user-cards", response_model=ApiResponse[UserCardResponse], status_code=201)
async def add_user_card(body: UserCardCreate, user: CurrentUser, session: Session):
    service = CardService(session)
    return ApiResponse(data=await service.add_user_card(user.id, body))


@router.delete("/user-cards/{user_card_id}", response_model=ApiResponse[None])
async def remove_user_card(user_card_id: int, user: CurrentUser, session: Session):
    service = CardService(session)
    await service.remove_user_card(user_card_id, user.id)
    return ApiResponse(data=None)
