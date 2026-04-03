import time
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.enums import SetSource
from src.app.models.set import Set, SetItem
from src.app.models.set_comment import SetComment
from src.app.models.user import User
from src.app.repositories.catalog import CatalogRepository
from src.app.schemas.catalog import (
    SetCommentCreate,
    SetCommentResponse,
    SetCreate,
    SetItemResponse,
    SetListItem,
    SetResponse,
    SetUpdate,
)
from src.app.schemas.user import AuthorInfo


def _compute_monthly(item) -> Decimal:
    """Рассчитать месячную стоимость позиции."""
    if hasattr(item, 'base_price') and item.base_price and hasattr(item, 'period_years') and item.period_years:
        qty = item.qty if item.qty else Decimal("1")
        return round((item.base_price * qty) / (item.period_years * 12), 2)
    if hasattr(item, 'price') and item.price:
        if hasattr(item, 'wear_life_weeks') and item.wear_life_weeks and item.item_type == "wear":
            months = Decimal(item.wear_life_weeks) / Decimal("4.33")
            if months > 0:
                return round(Decimal(item.price) / months, 2)
        if hasattr(item, 'daily_use') and item.daily_use and item.qty and item.item_type == "consumable":
            days_supply = item.qty / item.daily_use
            if days_supply > 0:
                return round(Decimal(item.price) / (days_supply / Decimal("30.44")), 2)
    return Decimal("0")


def _author_info(user) -> AuthorInfo | None:
    if user is None:
        return None
    if user.deleted_at is not None:
        return AuthorInfo(
            id=user.id, display_name="👻 Привидение",
            initials="👻", color=user.color,
        )
    return AuthorInfo(
        id=user.id, display_name=user.display_name,
        username=user.username,
        initials=user.initials, color=user.color,
        avatar_url=user.avatar_url,
    )


def _set_to_response(s: Set) -> SetResponse:
    items = [
        SetItemResponse(
            id=i.id, name=i.name, note=i.note, item_type=i.item_type,
            price=i.price or 0,
            qty=i.qty, unit=i.unit, daily_use=i.daily_use,
            wear_life_weeks=i.wear_life_weeks, purchase_date=i.purchase_date,
            planned_price=i.planned_price,
            base_price=i.base_price, period_years=i.period_years,
            monthly_cost=_compute_monthly(i),
        )
        for i in (s.items or [])
    ]
    return SetResponse(
        id=s.id, source=s.source, category_id=s.category_id,
        set_type=s.set_type, color=s.color, title=s.title,
        description=s.description, amount=s.amount,
        amount_label=s.amount_label, users_count=s.users_count,
        added=s.added, is_private=s.is_private, hidden=s.hidden,
        about_title=s.about_title, about_text=s.about_text,
        items=items, author=_author_info(s.author),
        created_at=s.created_at, updated_at=s.updated_at,
    )


def _set_to_list_item(s: Set) -> SetListItem:
    return SetListItem(
        id=s.id, source=s.source, category_id=s.category_id,
        set_type=s.set_type, color=s.color, title=s.title,
        description=s.description, amount=s.amount,
        amount_label=s.amount_label, users_count=s.users_count,
        is_private=s.is_private,
        items_count=len(s.items) if s.items else 0,
        author=_author_info(s.author),
        created_at=s.created_at,
    )


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CatalogRepository(session)

    async def list_sets(
        self, category_id: str | None = None, source: str | None = None,
        set_type: str | None = None, search: str | None = None,
        sort: str = "newest", limit: int = 20, offset: int = 0,
    ) -> tuple[list[SetListItem], int]:
        sets, total = await self._repo.list_public(
            category_id=category_id, source=source, set_type=set_type,
            search=search, sort=sort, limit=limit, offset=offset,
        )
        return [_set_to_list_item(s) for s in sets], total

    async def get_set(self, set_id: str) -> SetResponse:
        s = await self._repo.get_by_id(set_id)
        if s is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")
        return _set_to_response(s)

    async def create_set(self, user: User, data: SetCreate) -> SetResponse:
        set_id = f"u_{int(time.time() * 1000)}"
        source = SetSource.OWN

        s = Set(
            id=set_id, source=source.value, category_id=data.category_id,
            set_type=data.set_type, color=data.color, title=data.title,
            description=data.description, is_private=data.is_private,
            author_id=user.id, about_title=data.about_title,
            about_text=data.about_text,
        )
        await self._repo.create(s)

        if data.items:
            set_items = [
                SetItem(
                    set_id=set_id, name=item.name, note=item.note,
                    item_type=item.item_type, price=item.price,
                    qty=item.qty, unit=item.unit, daily_use=item.daily_use,
                    wear_life_weeks=item.wear_life_weeks,
                    purchase_date=item.purchase_date,
                    planned_price=item.planned_price,
                    base_price=item.base_price, period_years=item.period_years,
                )
                for item in data.items
            ]
            await self._repo.add_items(set_items)

        total = sum(int(_compute_monthly(i)) for i in (s.items or [])) if False else 0
        if data.items:
            await self._session.commit()
            self._session.expire_all()
            refreshed = await self._repo.get_by_id(set_id)
            total = sum(int(_compute_monthly(i)) for i in (refreshed.items or []))

        if total > 0:
            stmt = sa_update(Set).where(Set.id == set_id).values(
                amount=total, amount_label="руб / месяц"
            )
            await self._session.execute(stmt)

        await self._session.commit()
        self._session.expire_all()
        return await self.get_set(set_id)

    async def update_set(self, set_id: str, user: User, data: SetUpdate) -> SetResponse:
        s = await self._repo.get_by_id(set_id)
        if s is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")
        if s.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your set")
        if s.source != SetSource.OWN.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only private sets can be edited",
            )

        updates: dict = {}
        if data.title is not None:
            updates["title"] = data.title
        if data.description is not None:
            updates["description"] = data.description
        if data.about_title is not None:
            updates["about_title"] = data.about_title
        if data.about_text is not None:
            updates["about_text"] = data.about_text

        if updates:
            stmt = sa_update(Set).where(Set.id == set_id).values(**updates)
            await self._session.execute(stmt)

        if data.items is not None:
            await self._repo.delete_items_by_set(set_id)
            new_items = [
                SetItem(
                    set_id=set_id, name=item.name, note=item.note,
                    item_type=item.item_type, price=item.price,
                    qty=item.qty, unit=item.unit, daily_use=item.daily_use,
                    wear_life_weeks=item.wear_life_weeks,
                    purchase_date=item.purchase_date,
                    planned_price=item.planned_price,
                    base_price=item.base_price, period_years=item.period_years,
                )
                for item in data.items
            ]
            await self._repo.add_items(new_items)
            await self._session.flush()
            self._session.expire_all()
            refreshed = await self._repo.get_by_id(set_id)
            total = sum(int(_compute_monthly(i)) for i in (refreshed.items or []))
            stmt = sa_update(Set).where(Set.id == set_id).values(amount=total, amount_label="руб / месяц")
            await self._session.execute(stmt)

        await self._session.commit()
        self._session.expire_all()
        return await self.get_set(set_id)

    async def hide_set(self, set_id: str, user: User) -> None:
        s = await self._repo.get_by_id(set_id)
        if s is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")
        if s.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your set")
        stmt = sa_update(Set).where(Set.id == set_id).values(hidden=True)
        await self._session.execute(stmt)
        await self._session.commit()

    async def delete_set(self, set_id: str, user: User) -> None:
        s = await self._repo.get_by_id(set_id)
        if s is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")
        if s.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your set")
        if s.source != SetSource.OWN.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Public sets cannot be deleted, only hidden",
            )
        await self._repo.delete_set(set_id)
        await self._session.commit()

    async def list_comments(
        self, set_id: str, sort: str = "new", limit: int = 50, offset: int = 0
    ) -> tuple[list[SetCommentResponse], int]:
        comments, total = await self._repo.list_comments(set_id, sort, limit, offset)
        return [
            SetCommentResponse(
                id=c.id, set_id=c.set_id,
                user_id=str(c.user_id) if c.user_id else None,
                initials=c.initials, name=c.name, text=c.text,
                likes_count=c.likes_count, dislikes_count=c.dislikes_count,
                created_at=c.created_at,
            )
            for c in comments
        ], total

    async def add_comment(
        self, set_id: str, user: User, data: SetCommentCreate
    ) -> SetCommentResponse:
        s = await self._repo.get_by_id(set_id)
        if s is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")

        comment = SetComment(
            set_id=set_id, user_id=user.id,
            initials=user.initials, name=user.display_name,
            text=data.text,
        )
        comment = await self._repo.add_comment(comment)
        await self._session.commit()
        return SetCommentResponse(
            id=comment.id, set_id=comment.set_id,
            user_id=str(comment.user_id),
            initials=comment.initials, name=comment.name,
            text=comment.text, likes_count=comment.likes_count,
            dislikes_count=comment.dislikes_count,
            created_at=comment.created_at,
        )

    async def delete_comment(self, comment_id: int, user: User) -> None:
        comment = await self._repo.get_comment(comment_id)
        if comment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        if comment.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your comment")
        await self._repo.delete_comment(comment_id)
        await self._session.commit()
