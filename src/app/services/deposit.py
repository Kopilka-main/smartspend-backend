from fastapi import HTTPException, status
from sqlalchemy import func as sa_func
from sqlalchemy import or_, select
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
        # доход = заранее рассчитанный коэффициент income_coef[срок] × сумма
        coefs = deposit.income_coef or {}
        raw = coefs.get(str(months))
        if raw is None:
            return 0.0, 0.0
        try:
            coef = float(raw)
        except (ValueError, TypeError):
            return 0.0, 0.0
        if deposit.max_amount is not None and amount > deposit.max_amount:
            amount = deposit.max_amount
        income = round(amount * coef, 2)
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
            bank_logo_url=d.bank_logo_url,
            name=d.name,
            rates=d.rates,
            ear=d.ear,
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
        banks: list[str] | None = None,
        freq: list[str] | None = None,
        conditions: list[str] | None = None,
        liquidity: list[str] | None = None,
        sort: str = "bank",
        amount: float | None = None,
        months: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[DepositResponse], int]:
        query = select(Deposit).where(Deposit.is_active.is_(True))

        if search:
            query = query.where(Deposit.bank_name.ilike(f"%{search}%"))
        if banks:
            query = query.where(Deposit.bank_name.in_(banks))
        if freq:
            query = query.where(Deposit.freq.in_(freq))
        if liquidity:
            if "replenishment" in liquidity or "both" in liquidity:
                query = query.where(Deposit.replenishment.is_(True))
            if "withdrawal" in liquidity or "both" in liquidity:
                query = query.where(Deposit.withdrawal.is_(True))
        if conditions:
            query = query.where(or_(Deposit.conditions.is_(None), Deposit.conditions.contained_by(conditions)))

        count_q = query.with_only_columns(sa_func.count(Deposit.id))
        total = (await self._session.execute(count_q)).scalar() or 0

        result = await self._session.execute(query)
        all_deposits = list(result.scalars().all())

        if months is not None:
            all_deposits = [d for d in all_deposits if str(months) in (d.rates or {})]
            total = len(all_deposits)

        if amount is not None:
            all_deposits = [d for d in all_deposits if d.min_amount is None or amount >= d.min_amount]
            total = len(all_deposits)

        items = [self._to_response(d, amount, months) for d in all_deposits]

        if sort == "rate":
            if months is not None:
                items.sort(key=lambda x: float((x.ear or {}).get(str(months)) or 0), reverse=True)
            else:
                items.sort(key=lambda x: x.max_rate or 0, reverse=True)
        elif sort == "income" and amount is not None and months is not None:
            items.sort(key=lambda x: x.calc_income or 0, reverse=True)
        else:
            items.sort(key=lambda x: x.bank_name)

        items = items[offset : offset + limit]
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
        freq: list[str] | None = None,
        conditions: list[str] | None = None,
        liquidity: list[str] | None = None,
    ) -> list[DepositChartPoint]:
        query = select(Deposit).where(Deposit.is_active.is_(True))
        if bank_names:
            query = query.where(Deposit.bank_name.in_(bank_names))
        if freq:
            query = query.where(Deposit.freq.in_(freq))
        if conditions:
            query = query.where(or_(Deposit.conditions.is_(None), Deposit.conditions.contained_by(conditions)))
        if liquidity:
            if "replenishment" in liquidity or "both" in liquidity:
                query = query.where(Deposit.replenishment.is_(True))
            if "withdrawal" in liquidity or "both" in liquidity:
                query = query.where(Deposit.withdrawal.is_(True))

        result = await self._session.execute(query)
        deposits = result.scalars().all()

        periods = [
            (1, "1 мес"),
            (2, "2 мес"),
            (3, "3 мес"),
            (4, "4 мес"),
            (5, "5 мес"),
            (6, "6 мес"),
            (7, "7 мес"),
            (8, "8 мес"),
            (9, "9 мес"),
            (10, "10 мес"),
            (11, "11 мес"),
            (12, "1 год"),
            (18, "1.5 года"),
            (24, "2 года"),
            (36, "3 года"),
        ]

        points = []
        for months, label in periods:
            best = 0.0
            for d in deposits:
                raw = (d.rates or {}).get(str(months))
                if raw is None:
                    continue
                try:
                    rate = float(raw)
                except (ValueError, TypeError):
                    continue
                if rate > best:
                    best = rate
            points.append(DepositChartPoint(months=months, label=label, max_rate=best))

        return points
