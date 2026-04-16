import time
from decimal import Decimal
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.enums import SetSource
from src.app.models.envelope_category import EnvelopeCategory
from src.app.models.set import Set, SetItem
from src.app.models.set_comment import SetComment
from src.app.models.set_photo import SetPhoto
from src.app.models.user import User
from src.app.repositories.catalog import CatalogRepository
from src.app.schemas.catalog import (
    SetCommentCreate,
    SetCommentResponse,
    SetCreate,
    SetItemResponse,
    SetListItem,
    SetPhotoResponse,
    SetResponse,
    SetUpdate,
)
from src.app.schemas.user import AuthorInfo


def _compute_monthly(item) -> Decimal:
    price = getattr(item, "price", 0) or 0
    item_type = getattr(item, "item_type", "consumable")

    if item_type == "wear":
        weeks = getattr(item, "wear_life_weeks", None)
        if weeks and weeks > 0:
            months = Decimal(weeks) / Decimal("4.33")
            return round(Decimal(price) / months, 2)
        bp = getattr(item, "base_price", None)
        py = getattr(item, "period_years", None)
        if bp and py and py > 0:
            return round(Decimal(bp) / (Decimal(py) * 12), 2)
        return Decimal("0")

    daily = getattr(item, "daily_use", None)
    qty = getattr(item, "qty", None)
    if daily and qty and daily > 0 and qty > 0:
        days_supply = Decimal(str(qty)) / Decimal(str(daily))
        if days_supply > 0:
            return round(Decimal(price) / (days_supply / Decimal("30.44")), 2)

    bp = getattr(item, "base_price", None)
    py = getattr(item, "period_years", None)
    if bp and py and py > 0:
        q = Decimal(str(qty)) if qty else Decimal("1")
        return round((Decimal(bp) * q) / (Decimal(py) * 12), 2)

    if price > 0:
        return Decimal(price)

    return Decimal("0")


def _author_info(user) -> AuthorInfo | None:
    if user is None:
        return None
    if user.deleted_at is not None:
        return AuthorInfo(
            id=user.id,
            display_name="👻 Привидение",
            initials="👻",
            color=user.color,
        )
    return AuthorInfo(
        id=user.id,
        display_name=user.display_name,
        username=user.username,
        initials=user.initials,
        color=user.color,
        avatar_url=user.avatar_url,
    )


def _set_to_response(s: Set, category_name: str | None = None, comments_count: int = 0) -> SetResponse:
    items = [
        SetItemResponse(
            id=i.id,
            name=i.name,
            note=i.note,
            item_type=i.item_type,
            price=i.price or 0,
            qty=i.qty,
            unit=i.unit,
            daily_use=i.daily_use,
            wear_life_weeks=i.wear_life_weeks,
            purchase_date=i.purchase_date,
            planned_price=i.planned_price,
            base_price=i.base_price,
            period_years=i.period_years,
            monthly_cost=_compute_monthly(i),
        )
        for i in (s.items or [])
    ]
    photos = [
        SetPhotoResponse(id=p.id, url=p.url, file_name=p.file_name, position=p.position, created_at=p.created_at)
        for p in (s.photos or [])
    ]
    return SetResponse(
        id=s.id,
        source=s.source,
        category_id=s.category_id,
        category_name=category_name,
        set_type=s.set_type,
        color=s.color,
        title=s.title,
        description=s.description,
        amount=s.amount,
        amount_label=s.amount_label,
        monthly=s.monthly,
        full_cost=s.full_cost,
        period=s.period,
        users_count=s.users_count,
        comments_count=comments_count,
        likes_count=s.likes_count,
        dislikes_count=s.dislikes_count,
        added=s.added,
        is_private=s.is_private,
        hidden=s.hidden,
        status=getattr(s, "status", "published"),
        about_title=s.about_title,
        about_text=s.about_text,
        items=items,
        photos=photos,
        author=_author_info(s.author),
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


def _set_to_list_item(s: Set, category_name: str | None = None, comments_count: int = 0) -> SetListItem:
    items = [
        SetItemResponse(
            id=i.id,
            name=i.name,
            note=i.note,
            item_type=i.item_type,
            price=i.price or 0,
            qty=i.qty,
            unit=i.unit,
            daily_use=i.daily_use,
            wear_life_weeks=i.wear_life_weeks,
            purchase_date=i.purchase_date,
            planned_price=i.planned_price,
            base_price=i.base_price,
            period_years=i.period_years,
            monthly_cost=_compute_monthly(i),
        )
        for i in (s.items or [])
    ]
    return SetListItem(
        id=s.id,
        source=s.source,
        category_id=s.category_id,
        category_name=category_name,
        set_type=s.set_type,
        color=s.color,
        title=s.title,
        description=s.description,
        amount=s.amount,
        amount_label=s.amount_label,
        monthly=s.monthly,
        full_cost=s.full_cost,
        period=s.period,
        users_count=s.users_count,
        comments_count=comments_count,
        likes_count=s.likes_count,
        dislikes_count=s.dislikes_count,
        is_private=s.is_private,
        items_count=len(s.items) if s.items else 0,
        items=items,
        author=_author_info(s.author),
        created_at=s.created_at,
    )


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CatalogRepository(session)
        self._cat_cache: dict[str, str] | None = None

    async def _get_category_names(self) -> dict[str, str]:
        if self._cat_cache is None:
            from sqlalchemy import select

            result = await self._session.execute(select(EnvelopeCategory.id, EnvelopeCategory.name))
            self._cat_cache = dict(result.all())
        return self._cat_cache

    async def _enrich_list(self, sets: list[Set]) -> list[SetListItem]:
        cats = await self._get_category_names()
        result = []
        for s in sets:
            cc = len(s.comments) if s.comments else 0
            result.append(_set_to_list_item(s, category_name=cats.get(s.category_id), comments_count=cc))
        return result

    async def list_sets(
        self,
        category_id: str | None = None,
        source: str | None = None,
        set_type: str | None = None,
        search: str | None = None,
        sort: str = "newest",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[SetListItem], int]:
        sets, total = await self._repo.list_public(
            category_id=category_id,
            source=source,
            set_type=set_type,
            search=search,
            sort=sort,
            limit=limit,
            offset=offset,
        )
        return await self._enrich_list(sets), total

    async def list_by_author(self, author_id) -> tuple[list[SetListItem], int]:
        sets, total = await self._repo.list_by_author(author_id)
        return await self._enrich_list(sets), total

    async def get_set(self, set_id: str) -> SetResponse:
        s = await self._repo.get_by_id(set_id)
        if s is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")
        cats = await self._get_category_names()
        cc = len(s.comments) if s.comments else 0
        return _set_to_response(s, category_name=cats.get(s.category_id), comments_count=cc)

    async def create_set(self, user: User, data: SetCreate) -> SetResponse:
        set_id = f"u_{int(time.time() * 1000)}"
        source = SetSource.OWN

        s = Set(
            id=set_id,
            source=source.value,
            category_id=data.category_id,
            set_type=data.set_type,
            color=data.color,
            title=data.title,
            description=data.description,
            is_private=data.is_private,
            status=data.status,
            period=data.period,
            full_cost=data.full_cost,
            author_id=user.id,
            about_title=data.about_title,
            about_text=data.about_text,
        )
        await self._repo.create(s)

        if data.items:
            set_items = [
                SetItem(
                    set_id=set_id,
                    name=item.name,
                    note=item.note,
                    item_type=item.item_type,
                    price=item.price,
                    qty=item.qty,
                    unit=item.unit,
                    daily_use=item.daily_use,
                    wear_life_weeks=item.wear_life_weeks,
                    purchase_date=item.purchase_date,
                    planned_price=item.planned_price,
                    base_price=item.base_price,
                    period_years=item.period_years,
                )
                for item in data.items
            ]
            await self._repo.add_items(set_items)

        total = 0
        if data.items:
            await self._session.commit()
            self._session.expire_all()
            refreshed = await self._repo.get_by_id(set_id)
            total = sum(int(_compute_monthly(i)) for i in (refreshed.items or []))

        stmt = sa_update(Set).where(Set.id == set_id).values(amount=total, amount_label="руб / месяц")
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
                    set_id=set_id,
                    name=item.name,
                    note=item.note,
                    item_type=item.item_type,
                    price=item.price,
                    qty=item.qty,
                    unit=item.unit,
                    daily_use=item.daily_use,
                    wear_life_weeks=item.wear_life_weeks,
                    purchase_date=item.purchase_date,
                    planned_price=item.planned_price,
                    base_price=item.base_price,
                    period_years=item.period_years,
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
                id=c.id,
                set_id=c.set_id,
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

    async def add_comment(self, set_id: str, user: User, data: SetCommentCreate) -> SetCommentResponse:
        s = await self._repo.get_by_id(set_id)
        if s is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")

        comment = SetComment(
            set_id=set_id,
            user_id=user.id,
            initials=user.initials,
            name=user.display_name,
            text=data.text,
            parent_id=data.parent_id,
        )
        comment = await self._repo.add_comment(comment)
        await self._session.commit()
        return SetCommentResponse(
            id=comment.id,
            set_id=comment.set_id,
            user_id=str(comment.user_id),
            parent_id=comment.parent_id,
            initials=comment.initials,
            name=comment.name,
            text=comment.text,
            likes_count=comment.likes_count,
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

    async def add_photo(self, set_id: str, user: User, file: UploadFile) -> SetPhotoResponse:
        s = await self._repo.get_by_id(set_id)
        if s is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")
        if s.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your set")

        allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
        if file.content_type not in allowed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type")

        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 5 MB)")

        ext = Path(file.filename or "photo.jpg").suffix or ".jpg"
        unique_name = f"{set_id}_{int(time.time() * 1000)}{ext}"
        upload_dir = Path("/app/uploads/set_photos") / set_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(upload_dir / unique_name, "wb") as f:
            await f.write(content)

        url = f"/uploads/set_photos/{set_id}/{unique_name}"
        position = len(s.photos) if s.photos else 0
        photo = SetPhoto(set_id=set_id, url=url, file_name=file.filename or unique_name, position=position)
        self._session.add(photo)
        await self._session.flush()
        await self._session.refresh(photo)
        await self._session.commit()
        return SetPhotoResponse(
            id=photo.id, url=photo.url, file_name=photo.file_name, position=photo.position, created_at=photo.created_at
        )

    async def delete_photo(self, photo_id: int, user: User) -> None:
        photo = await self._session.get(SetPhoto, photo_id)
        if photo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
        s = await self._repo.get_by_id(photo.set_id)
        if s is None or s.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your set")
        file_path = Path("/app") / photo.url.lstrip("/")
        if file_path.exists():
            file_path.unlink()
        await self._session.delete(photo)
        await self._session.commit()

    async def bookmark(self, set_id: str, user_id) -> None:
        from src.app.models.saved_set import SavedSet

        s = await self._repo.get_by_id(set_id)
        if s is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")
        existing = await self._session.execute(
            select(SavedSet).where(SavedSet.user_id == user_id, SavedSet.set_id == set_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already bookmarked")
        self._session.add(SavedSet(user_id=user_id, set_id=set_id))
        await self._session.commit()

    async def unbookmark(self, set_id: str, user_id) -> None:
        from sqlalchemy import delete as sa_delete

        from src.app.models.saved_set import SavedSet

        result = await self._session.execute(
            sa_delete(SavedSet).where(SavedSet.user_id == user_id, SavedSet.set_id == set_id)
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not bookmarked")
        await self._session.commit()
