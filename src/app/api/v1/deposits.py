from fastapi import APIRouter, Query

from src.app.core.dependencies import CurrentUser, Session
from src.app.schemas.base import ApiResponse, PaginationMeta
from src.app.schemas.deposit import (
    DepositCalculation,
    DepositCommentCreate,
    DepositCommentResponse,
    DepositResponse,
)
from src.app.services.deposit import DepositService

router = APIRouter(prefix="/deposits", tags=["deposits"])


@router.get("", response_model=ApiResponse[list[DepositResponse]])
async def list_deposits(
    session: Session,
    search: str | None = Query(None, alias="q"),
    freq: str | None = Query(None),
    conditions: str | None = Query(None),
    replenishment: bool | None = Query(None),
    sort: str = Query("bank"),
    amount: float | None = Query(None, ge=0),
    months: int | None = Query(None, ge=1),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    service = DepositService(session)
    items, total = await service.list_deposits(
        search=search,
        freq=freq,
        conditions=conditions,
        replenishment=replenishment,
        sort=sort,
        amount=amount,
        months=months,
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


@router.get("/{deposit_id}/comments", response_model=ApiResponse[list[DepositCommentResponse]])
async def list_deposit_comments(
    deposit_id: str,
    session: Session,
    sort: str = Query("new"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    service = DepositService(session)
    comments, total = await service.list_comments(deposit_id, sort, limit, offset)
    return ApiResponse(
        data=comments,
        meta=PaginationMeta(total=total, limit=limit, offset=offset).model_dump(by_alias=True),
    )


@router.post("/{deposit_id}/comments", response_model=ApiResponse[DepositCommentResponse], status_code=201)
async def add_deposit_comment(
    deposit_id: str,
    body: DepositCommentCreate,
    user: CurrentUser,
    session: Session,
):
    service = DepositService(session)
    return ApiResponse(data=await service.add_comment(deposit_id, user, body))


@router.delete("/comments/{comment_id}", response_model=ApiResponse[None])
async def delete_deposit_comment(comment_id: int, user: CurrentUser, session: Session):
    service = DepositService(session)
    await service.delete_comment(comment_id, user)
    return ApiResponse(data=None)
