import uuid

from fastapi import HTTPException, status
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.company import Company
from src.app.models.promo import Promo, PromoComment, PromoVote
from src.app.models.user import User
from src.app.schemas.company import CompanyResponse
from src.app.schemas.promo import (
    PromoCommentCreate,
    PromoCommentResponse,
    PromoCreate,
    PromoResponse,
)


class PromoService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _enrich_promo(self, promo: Promo) -> PromoResponse:
        company = None
        if promo.company_id:
            c = await self._session.get(Company, promo.company_id)
            if c:
                company = CompanyResponse.model_validate(c)

        return PromoResponse(
            id=promo.id,
            type=promo.type,
            company_id=promo.company_id,
            category_id=promo.category_id,
            author_id=str(promo.author_id) if promo.author_id else None,
            text=promo.text,
            channel=promo.channel,
            url=promo.url,
            conditions=promo.conditions,
            expires_at=promo.expires_at,
            votes_up=promo.votes_up,
            votes_down=promo.votes_down,
            is_active=promo.is_active,
            created_at=promo.created_at,
            company=company,
        )

    async def list_promos(
        self,
        promo_type: str | None = None,
        scope: str = "all",
        category_id: str | None = None,
        condition: str | None = None,
        user_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[PromoResponse], int]:
        query = select(Promo).where(Promo.is_active.is_(True))

        if promo_type:
            query = query.where(Promo.type == promo_type)
        if scope == "mine" and user_id:
            query = query.where(Promo.author_id == user_id)
        if category_id:
            query = query.where(Promo.category_id == category_id)
        if condition:
            query = query.where(Promo.conditions.any(condition))

        count_q = query.with_only_columns(Promo.id)
        count_result = await self._session.execute(count_q)
        total = len(count_result.all())

        query = query.order_by(Promo.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(query)
        promos = result.scalars().all()

        return [await self._enrich_promo(p) for p in promos], total

    async def get_promo(self, promo_id: int) -> PromoResponse:
        promo = await self._session.get(Promo, promo_id)
        if promo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo not found")
        return await self._enrich_promo(promo)

    async def create_promo(self, user: User, data: PromoCreate) -> PromoResponse:
        promo = Promo(
            type=data.type,
            company_id=data.company_id,
            category_id=data.category_id,
            author_id=user.id,
            text=data.text,
            conditions=data.conditions,
            expires_at=data.expires_at,
        )
        self._session.add(promo)
        await self._session.flush()
        await self._session.refresh(promo)
        await self._session.commit()
        return await self._enrich_promo(promo)

    async def vote(self, promo_id: int, user_id: uuid.UUID, vote: str) -> PromoResponse:
        promo = await self._session.get(Promo, promo_id)
        if promo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo not found")

        existing = await self._session.execute(
            select(PromoVote).where(PromoVote.user_id == user_id, PromoVote.promo_id == promo_id)
        )
        old_vote = existing.scalar_one_or_none()

        if old_vote:
            if old_vote.vote == vote:
                await self._session.execute(sa_delete(PromoVote).where(PromoVote.id == old_vote.id))
            else:
                await self._session.execute(sa_update(PromoVote).where(PromoVote.id == old_vote.id).values(vote=vote))
        else:
            self._session.add(PromoVote(user_id=user_id, promo_id=promo_id, vote=vote))

        await self._session.flush()
        await self._sync_votes(promo_id)
        await self._session.commit()

        return await self.get_promo(promo_id)

    async def _sync_votes(self, promo_id: int) -> None:
        up_result = await self._session.execute(
            select(PromoVote.id).where(PromoVote.promo_id == promo_id, PromoVote.vote == "up")
        )
        down_result = await self._session.execute(
            select(PromoVote.id).where(PromoVote.promo_id == promo_id, PromoVote.vote == "down")
        )
        await self._session.execute(
            sa_update(Promo)
            .where(Promo.id == promo_id)
            .values(votes_up=len(up_result.all()), votes_down=len(down_result.all()))
        )

    async def list_comments(
        self,
        promo_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[PromoCommentResponse], int]:
        query = select(PromoComment).where(PromoComment.promo_id == promo_id)

        count_q = query.with_only_columns(PromoComment.id)
        count_result = await self._session.execute(count_q)
        total = len(count_result.all())

        query = query.order_by(PromoComment.created_at.asc()).limit(limit).offset(offset)
        result = await self._session.execute(query)
        comments = result.scalars().all()

        return [
            PromoCommentResponse(
                id=c.id,
                promo_id=c.promo_id,
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

    async def add_comment(self, promo_id: int, user: User, data: PromoCommentCreate) -> PromoCommentResponse:
        promo = await self._session.get(Promo, promo_id)
        if promo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo not found")

        comment = PromoComment(
            promo_id=promo_id,
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

        return PromoCommentResponse(
            id=comment.id,
            promo_id=comment.promo_id,
            user_id=str(comment.user_id),
            parent_id=comment.parent_id,
            initials=comment.initials,
            name=comment.name,
            text=comment.text,
            likes_count=comment.likes_count,
            dislikes_count=comment.dislikes_count,
            created_at=comment.created_at,
        )

    async def delete_comment(self, comment_id: int, user_id: uuid.UUID) -> None:
        comment = await self._session.get(PromoComment, comment_id)
        if comment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        if comment.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your comment")
        await self._session.execute(sa_delete(PromoComment).where(PromoComment.id == comment_id))
        await self._session.commit()
