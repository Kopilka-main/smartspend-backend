import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import delete as sa_delete
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.company import Company, UserCompany
from src.app.models.envelope_category import EnvelopeCategory
from src.app.models.promo import Promo, PromoComment, PromoVote
from src.app.models.user import User
from src.app.repositories.article import ArticleRepository
from src.app.repositories.catalog import CatalogRepository
from src.app.repositories.follow import FollowRepository
from src.app.schemas.company import CompanyResponse
from src.app.schemas.promo import (
    PromoCommentCreate,
    PromoCommentResponse,
    PromoCreate,
    PromoResponse,
    PromoVoteEntry,
)
from src.app.schemas.user import AuthorInfo


class PromoService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _get_cat_names(self) -> dict[str, str]:
        result = await self._session.execute(select(EnvelopeCategory.id, EnvelopeCategory.name))
        return dict(result.all())

    async def _enrich_promo(
        self,
        promo: Promo,
        cats: dict[str, str] | None = None,
        viewer_id: uuid.UUID | None = None,
    ) -> PromoResponse:
        if cats is None:
            cats = await self._get_cat_names()

        company = None
        if promo.company_id:
            c = await self._session.get(Company, promo.company_id)
            if c:
                company = CompanyResponse(
                    id=c.id,
                    name=c.name,
                    abbr=c.abbr,
                    color=c.color,
                    category_id=c.category_id,
                    category_name=cats.get(c.category_id) if c.category_id else None,
                    description=c.description,
                    promo_types=c.promo_types,
                )

        comments_count = (
            await self._session.execute(select(sa_func.count(PromoComment.id)).where(PromoComment.promo_id == promo.id))
        ).scalar() or 0

        my_vote = None
        if viewer_id:
            vote_row = (
                await self._session.execute(
                    select(PromoVote.vote).where(PromoVote.promo_id == promo.id, PromoVote.user_id == viewer_id)
                )
            ).scalar_one_or_none()
            my_vote = vote_row

        history_rows = (
            await self._session.execute(
                select(PromoVote.user_id, PromoVote.vote, PromoVote.created_at)
                .where(PromoVote.promo_id == promo.id)
                .order_by(PromoVote.created_at.desc())
                .limit(40)
            )
        ).all()
        vote_history = [PromoVoteEntry(user_id=str(r[0]), vote=r[1], created_at=r[2]) for r in reversed(history_rows)]

        author = None
        if promo.author_id:
            u = await self._session.get(User, promo.author_id)
            if u:
                fc = await FollowRepository(self._session).count_followers(u.id)
                ac = await ArticleRepository(self._session).count_by_author(u.id)
                _, sc = await CatalogRepository(self._session).list_by_author(u.id, limit=0, offset=0)
                author = AuthorInfo(
                    id=u.id,
                    display_name=u.display_name,
                    username=u.username,
                    initials=u.initials,
                    color=u.color,
                    avatar_url=u.avatar_url,
                    followers_count=fc,
                    articles_count=ac,
                    sets_count=sc,
                )

        return PromoResponse(
            id=promo.id,
            type=promo.type,
            company_id=promo.company_id,
            category_id=promo.category_id,
            category_name=cats.get(promo.category_id) if promo.category_id else None,
            author_id=str(promo.author_id) if promo.author_id else None,
            author=author,
            title=promo.title,
            text=promo.text,
            code=promo.code,
            channel=promo.channel,
            url=promo.url,
            source_url=promo.source_url,
            promo_filter=promo.promo_filter,
            conditions=promo.conditions,
            expires_at=promo.expires_at,
            votes_up=promo.votes_up,
            votes_down=promo.votes_down,
            comments_count=comments_count,
            my_vote=my_vote,
            vote_history=vote_history,
            is_active=promo.is_active,
            created_at=promo.created_at,
            company=company,
        )

    async def list_promos(
        self,
        promo_type: str | None = None,
        scope: str = "all",
        category_ids: list[str] | None = None,
        company_ids: list[str] | None = None,
        promo_filter: str | None = None,
        search: str | None = None,
        sort: str = "newest",
        user_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[PromoResponse], int]:
        query = select(Promo).where(Promo.is_active.is_(True))

        if promo_type and promo_type != "all":
            if promo_type == "official":
                query = query.where(Promo.type.in_(["event", "coupon"]))
            else:
                query = query.where(Promo.type == promo_type)

        if scope == "mine" and user_id:
            sub = select(UserCompany.company_id).where(UserCompany.user_id == user_id)
            query = query.where(Promo.company_id.in_(sub))

        if category_ids:
            query = query.where(Promo.category_id.in_(category_ids))
        if company_ids:
            query = query.where(Promo.company_id.in_(company_ids))
        if promo_filter and promo_filter != "all":
            query = query.where(Promo.promo_filter == promo_filter)
        if search:
            pattern = f"%{search}%"
            query = query.where(Promo.title.ilike(pattern) | Promo.text.ilike(pattern))

        count_q = query.with_only_columns(sa_func.count(Promo.id))
        total = (await self._session.execute(count_q)).scalar() or 0

        if sort == "newest":
            query = query.order_by(Promo.created_at.desc(), Promo.id.desc())
        elif sort in ("votes_7d", "votes_30d", "votes_all"):
            query = query.order_by((Promo.votes_up - Promo.votes_down).desc(), Promo.created_at.desc(), Promo.id.desc())

        query = query.limit(limit).offset(offset)
        result = await self._session.execute(query)
        promos = result.scalars().all()

        cats = await self._get_cat_names()

        if sort in ("votes_7d", "votes_30d"):
            now = datetime.now(UTC)
            days = 7 if sort == "votes_7d" else 30
            cutoff = now - timedelta(days=days)
            promos = [p for p in promos if p.created_at and p.created_at >= cutoff]

        return [await self._enrich_promo(p, cats, user_id) for p in promos], total

    async def get_promo(self, promo_id: int, viewer_id: uuid.UUID | None = None) -> PromoResponse:
        promo = await self._session.get(Promo, promo_id)
        if promo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo not found")
        return await self._enrich_promo(promo, viewer_id=viewer_id)

    async def create_promo(self, user: User, data: PromoCreate) -> PromoResponse:
        promo = Promo(
            type=data.type,
            company_id=data.company_id,
            category_id=data.category_id,
            author_id=user.id,
            title=data.title,
            text=data.text,
            code=data.code,
            source_url=data.source_url,
            channel=data.channel,
            promo_filter=data.promo_filter,
            conditions=data.conditions,
            expires_at=data.expires_at,
        )
        self._session.add(promo)
        await self._session.flush()
        await self._session.refresh(promo)
        await self._session.commit()
        return await self._enrich_promo(promo, viewer_id=user.id)

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

        return await self.get_promo(promo_id, viewer_id=user_id)

    async def _sync_votes(self, promo_id: int) -> None:
        up = (
            await self._session.execute(
                select(sa_func.count(PromoVote.id)).where(PromoVote.promo_id == promo_id, PromoVote.vote == "up")
            )
        ).scalar() or 0
        down = (
            await self._session.execute(
                select(sa_func.count(PromoVote.id)).where(PromoVote.promo_id == promo_id, PromoVote.vote == "down")
            )
        ).scalar() or 0
        await self._session.execute(sa_update(Promo).where(Promo.id == promo_id).values(votes_up=up, votes_down=down))

    async def list_comments(
        self,
        promo_id: int,
        sort: str = "new",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[PromoCommentResponse], int]:
        base = select(PromoComment).where(PromoComment.promo_id == promo_id)
        total = (await self._session.execute(base.with_only_columns(sa_func.count(PromoComment.id)))).scalar() or 0

        if sort == "top":
            order = (PromoComment.likes_count - PromoComment.dislikes_count).desc()
        elif sort == "old":
            order = PromoComment.created_at.asc()
        else:
            order = PromoComment.created_at.desc()

        result = await self._session.execute(base.order_by(order).limit(limit).offset(offset))
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
