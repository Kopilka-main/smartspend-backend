from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.deposit import Deposit
from src.app.schemas.deposit import DepositCalculation, DepositResponse


class DepositService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_deposits(
        self,
        freq: str | None = None,
        conditions: str | None = None,
        replenishment: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[DepositResponse], int]:
        query = select(Deposit).where(Deposit.is_active.is_(True))

        if freq:
            query = query.where(Deposit.freq == freq)
        if replenishment is not None:
            query = query.where(Deposit.replenishment.is_(replenishment))
        if conditions:
            query = query.where(Deposit.conditions.any(conditions))

        count_result = await self._session.execute(
            select(Deposit.id).where(Deposit.is_active.is_(True))
            if not any([freq, conditions, replenishment is not None])
            else query.with_only_columns(Deposit.id)
        )
        total = len(count_result.all())

        query = query.order_by(Deposit.bank_name).limit(limit).offset(offset)
        result = await self._session.execute(query)
        deposits = result.scalars().all()

        return [DepositResponse.model_validate(d) for d in deposits], total

    async def get_deposit(self, deposit_id: str) -> DepositResponse:
        deposit = await self._session.get(Deposit, deposit_id)
        if deposit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deposit not found")
        return DepositResponse.model_validate(deposit)

    async def calculate(self, deposit_id: str, amount: float, months: int) -> DepositCalculation:
        deposit = await self._session.get(Deposit, deposit_id)
        if deposit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deposit not found")

        rates = deposit.rates or {}
        rate = self._pick_rate(rates, months)

        if deposit.freq == "monthly":
            monthly_rate = rate / 100 / 12
            total = amount
            for _ in range(months):
                total += total * monthly_rate
            income = round(total - amount, 2)
            total_amount = round(total, 2)
        else:
            income = round(amount * (rate / 100) * (months / 12), 2)
            total_amount = round(amount + income, 2)

        return DepositCalculation(
            months=months,
            rate=rate,
            income=income,
            total_amount=total_amount,
        )

    @staticmethod
    def _pick_rate(rates: dict, months: int) -> float:
        best_rate = 0.0
        best_key = 0
        for key, val in rates.items():
            try:
                k = int(key)
            except (ValueError, TypeError):
                continue
            if k <= months and k >= best_key:
                best_key = k
                best_rate = float(val)
        return best_rate
