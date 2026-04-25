from fastapi import HTTPException, status
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.deposit import Deposit
from src.app.models.deposit_comment import DepositComment
from src.app.schemas.deposit import DepositCalculation, DepositChartPoint, DepositCommentResponse, DepositResponse


class DepositService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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

    @staticmethod
    def _max_rate(rates: dict) -> float:
        best = 0.0
        for val in rates.values():
            try:
                r = float(val)
            except (ValueError, TypeError):
                continue
            if r > best:
                best = r
        return best

    def _calc_income(self, deposit: Deposit, amount: float, months: int) -> tuple[float, float]:
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
        return income, total_amount

    def _to_response(self, d: Deposit, amount: float | None = None, months: int | None = None) -> DepositResponse:
        calc_income = None
        calc_total = None
        if amount is not None and months is not None:
            calc_income, calc_total = self._calc_income(d, amount, months)

        return DepositResponse(
            id=d.id,
            bank_name=d.bank_name,
            bank_color=d.bank_color,
            bank_text_color=d.bank_text_color,
            bank_abbr=d.bank_abbr,
            name=d.name,
            rates=d.rates,
            min_amount=d.min_amount,
            max_amount=d.max_amount,
            replenishment=d.replenishment,
            withdrawal=d.withdrawal,
            freq=d.freq,
            is_systemic=d.is_systemic,
            conditions=d.conditions,
            tags=d.tags,
            conditions_text=d.conditions_text,
            params=d.params,
            tariff=d.tariff,
            is_active=d.is_active,
            max_rate=self._max_rate(d.rates or {}),
            calc_income=calc_income,
            calc_total=calc_total,
        )

    async def list_deposits(
        self,
        search: str | None = None,
        freq: str | None = None,
        conditions: str | None = None,
        replenishment: bool | None = None,
        sort: str = "bank",
        amount: float | None = None,
        months: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[DepositResponse], int]:
        query = select(Deposit).where(Deposit.is_active.is_(True))

        if search:
            query = query.where(Deposit.bank_name.ilike(f"%{search}%"))
        if freq:
            query = query.where(Deposit.freq == freq)
        if replenishment is not None:
            query = query.where(Deposit.replenishment.is_(replenishment))
        if conditions:
            query = query.where(Deposit.conditions.any(conditions))

        count_q = query.with_only_columns(sa_func.count(Deposit.id))
        total = (await self._session.execute(count_q)).scalar() or 0

        query = query.limit(limit).offset(offset)
        result = await self._session.execute(query)
        deposits = list(result.scalars().all())

        items = [self._to_response(d, amount, months) for d in deposits]

        if sort == "rate":
            items.sort(key=lambda x: x.max_rate or 0, reverse=True)
        elif sort == "income" and amount is not None and months is not None:
            items.sort(key=lambda x: x.calc_income or 0, reverse=True)
        else:
            items.sort(key=lambda x: x.bank_name)

        return items, total

    async def get_deposit(self, deposit_id: str) -> DepositResponse:
        deposit = await self._session.get(Deposit, deposit_id)
        if deposit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deposit not found")
        return self._to_response(deposit)

    async def calculate(self, deposit_id: str, amount: float, months: int) -> DepositCalculation:
        deposit = await self._session.get(Deposit, deposit_id)
        if deposit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deposit not found")

        rates = deposit.rates or {}
        rate = self._pick_rate(rates, months)
        income, total_amount = self._calc_income(deposit, amount, months)

        return DepositCalculation(
            months=months,
            rate=rate,
            income=income,
            total_amount=total_amount,
        )

    async def list_comments(
        self, deposit_id: str, sort: str = "new", limit: int = 50, offset: int = 0
    ) -> tuple[list[DepositCommentResponse], int]:
        deposit = await self._session.get(Deposit, deposit_id)
        if deposit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deposit not found")

        base = select(DepositComment).where(DepositComment.deposit_id == deposit_id)
        total = (await self._session.execute(base.with_only_columns(sa_func.count(DepositComment.id)))).scalar() or 0

        order = DepositComment.created_at.desc() if sort == "new" else DepositComment.created_at.asc()
        result = await self._session.execute(base.order_by(order).limit(limit).offset(offset))
        comments = result.scalars().all()

        return [
            DepositCommentResponse(
                id=c.id,
                deposit_id=c.deposit_id,
                user_id=str(c.user_id) if c.user_id else None,
                parent_id=c.parent_id,
                initials=c.initials,
                name=c.name,
                text=c.text,
                likes_count=c.likes_count,
                dislikes_count=c.dislikes_count,
                created_at=c.created_at,
            )
            for c in comments
        ], total

    async def add_comment(self, deposit_id: str, user, data) -> DepositCommentResponse:
        deposit = await self._session.get(Deposit, deposit_id)
        if deposit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deposit not found")

        comment = DepositComment(
            deposit_id=deposit_id,
            user_id=user.id,
            initials=user.initials,
            name=user.display_name,
            text=data.text,
            parent_id=data.parent_id,
        )
        self._session.add(comment)
        await self._session.flush()
        await self._session.refresh(comment)
        await self._session.commit()

        return DepositCommentResponse(
            id=comment.id,
            deposit_id=comment.deposit_id,
            user_id=str(comment.user_id),
            parent_id=comment.parent_id,
            initials=comment.initials,
            name=comment.name,
            text=comment.text,
            likes_count=comment.likes_count,
            dislikes_count=comment.dislikes_count,
            created_at=comment.created_at,
        )

    async def delete_comment(self, comment_id: int, user) -> None:
        comment = await self._session.get(DepositComment, comment_id)
        if comment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        if comment.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your comment")
        await self._session.delete(comment)
        await self._session.commit()

    async def chart(
        self,
        bank_names: list[str] | None = None,
        freq: str | None = None,
        conditions: str | None = None,
        replenishment: bool | None = None,
    ) -> list[DepositChartPoint]:
        query = select(Deposit).where(Deposit.is_active.is_(True))
        if bank_names:
            query = query.where(Deposit.bank_name.in_(bank_names))
        if freq:
            query = query.where(Deposit.freq == freq)
        if conditions:
            query = query.where(Deposit.conditions.any(conditions))
        if replenishment is not None:
            query = query.where(Deposit.replenishment.is_(replenishment))

        result = await self._session.execute(query)
        deposits = result.scalars().all()

        periods = [
            (1, "1 мес"),
            (2, "2 мес"),
            (3, "3 мес"),
            (4, "4 мес"),
            (5, "5 мес"),
            (6, "6 мес"),
            (12, "1 год"),
            (18, "1.5 года"),
            (24, "2 года"),
            (36, "3 года"),
        ]

        points = []
        for months, label in periods:
            best = 0.0
            for d in deposits:
                rates = d.rates or {}
                rate = self._pick_rate(rates, months)
                if rate > best:
                    best = rate
            points.append(DepositChartPoint(months=months, label=label, max_rate=best))

        return points
