from fastapi import APIRouter, Query

from src.app.core.dependencies import Session
from src.app.schemas.base import ApiResponse, PaginationMeta
from src.app.schemas.deposit import DepositCalculation, DepositResponse
from src.app.services.deposit import DepositService

router = APIRouter(prefix="/deposits", tags=["deposits"])


@router.get("", response_model=ApiResponse[list[DepositResponse]])
async def list_deposits(
    session: Session,
    freq: str | None = Query(None),
    conditions: str | None = Query(None),
    replenishment: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    service = DepositService(session)
    items, total = await service.list_deposits(
        freq=freq,
        conditions=conditions,
        replenishment=replenishment,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        data=items,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.get("/{deposit_id}", response_model=ApiResponse[DepositResponse])
async def get_deposit(deposit_id: str, session: Session):
    service = DepositService(session)
    return ApiResponse(data=await service.get_deposit(deposit_id))


@router.get("/{deposit_id}/calculate", response_model=ApiResponse[DepositCalculation])
async def calculate_deposit(
    deposit_id: str,
    session: Session,
    amount: float = Query(ge=0),
    months: int = Query(ge=1),
):
    service = DepositService(session)
    return ApiResponse(data=await service.calculate(deposit_id, amount, months))
