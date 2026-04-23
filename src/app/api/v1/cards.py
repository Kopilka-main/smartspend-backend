from fastapi import APIRouter, Query

from src.app.core.dependencies import CurrentUser, OptionalUser, Session
from src.app.schemas.base import ApiResponse, PaginationMeta
from src.app.schemas.card import (
    CardCalculateRequest,
    CardCalculateResponse,
    CardResponse,
    SpendingUpdate,
    UserCardCreate,
    UserCardResponse,
)
from src.app.services.card import CardService

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/banks", response_model=ApiResponse[list[str]])
async def list_card_banks(session: Session):
    from sqlalchemy import select as sa_select

    from src.app.models.card import Card

    result = await session.execute(
        sa_select(Card.bank_name).where(Card.is_active.is_(True)).distinct().order_by(Card.bank_name)
    )
    return ApiResponse(data=[r[0] for r in result.all()])


@router.get("", response_model=ApiResponse[list[CardResponse]])
async def list_cards(
    session: Session,
    current_user: OptionalUser,
    card_type: str | None = Query(None, alias="cardType"),
    bank_name: str | None = Query(None, alias="bankName"),
    search: str | None = Query(None, alias="q"),
    condition: str | None = Query(None),
    scope: str = Query("all"),
    sort: str = Query("cashback"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    user_id = current_user.id if current_user else None
    spending = None
    if user_id:
        service = CardService(session)
        spending = await service.get_spending(user_id)

    service = CardService(session)
    items, total = await service.list_cards(
        card_type=card_type,
        bank_name=bank_name,
        search=search,
        condition=condition,
        scope=scope,
        sort=sort,
        spending=spending if spending else None,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        data=items,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.get("/spending", response_model=ApiResponse[dict])
async def get_spending(user: CurrentUser, session: Session):
    service = CardService(session)
    return ApiResponse(data=await service.get_spending(user.id))


@router.put("/spending", response_model=ApiResponse[dict])
async def update_spending(body: SpendingUpdate, user: CurrentUser, session: Session):
    service = CardService(session)
    return ApiResponse(data=await service.update_spending(user.id, body.spending))


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
