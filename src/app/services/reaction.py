import uuid

from fastapi import HTTPException, status
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.article import Article
from src.app.models.article_comment import ArticleComment
from src.app.models.enums import ReactionTarget, ReactionType
from src.app.models.set_comment import SetComment
from src.app.repositories.reaction import ReactionRepository
from src.app.schemas.reaction import ReactionCreate, ReactionResponse

VALID_TARGETS = {t.value for t in ReactionTarget}
VALID_TYPES = {t.value for t in ReactionType}


class ReactionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ReactionRepository(session)

    async def toggle_reaction(self, user_id: uuid.UUID, data: ReactionCreate) -> ReactionResponse | None:
        if data.target_type not in VALID_TARGETS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid target_type, must be one of: {', '.join(VALID_TARGETS)}",
            )
        if data.type not in VALID_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid type, must be one of: {', '.join(VALID_TYPES)}",
            )

        existing = await self._repo.find(user_id, data.target_type, data.target_id)

        if existing and existing.type == data.type:
            await self._repo.remove(user_id, data.target_type, data.target_id)
            await self._sync_counts(data.target_type, data.target_id)
            await self._session.commit()
            return None

        reaction = await self._repo.upsert(
            user_id,
            data.target_type,
            data.target_id,
            data.type,
        )
        await self._sync_counts(data.target_type, data.target_id)
        await self._session.commit()

        return ReactionResponse(
            id=reaction.id,
            user_id=str(reaction.user_id),
            target_type=reaction.target_type,
            target_id=reaction.target_id,
            type=reaction.type,
            created_at=reaction.created_at,
        )

    async def get_user_reactions(self, user_id: uuid.UUID, target_type: str | None = None) -> list[ReactionResponse]:
        reactions = await self._repo.list_by_user(user_id, target_type)
        return [
            ReactionResponse(
                id=r.id,
                user_id=str(r.user_id),
                target_type=r.target_type,
                target_id=r.target_id,
                type=r.type,
                created_at=r.created_at,
            )
            for r in reactions
        ]

    async def _sync_counts(self, target_type: str, target_id: str) -> None:
        likes = await self._repo.count(target_type, target_id, "like")
        dislikes = await self._repo.count(target_type, target_id, "dislike")

        if target_type == "article":
            stmt = sa_update(Article).where(Article.id == target_id).values(likes_count=likes, dislikes_count=dislikes)
            await self._session.execute(stmt)
        elif target_type == "set":
            pass
        elif target_type == "comment":
            try:
                comment_id = int(target_id)
            except ValueError:
                return
            ac = await self._session.get(ArticleComment, comment_id)
            if ac:
                stmt = (
                    sa_update(ArticleComment)
                    .where(ArticleComment.id == comment_id)
                    .values(likes_count=likes, dislikes_count=dislikes)
                )
                await self._session.execute(stmt)
            else:
                sc = await self._session.get(SetComment, comment_id)
                if sc:
                    stmt = (
                        sa_update(SetComment)
                        .where(SetComment.id == comment_id)
                        .values(likes_count=likes, dislikes_count=dislikes)
                    )
                    await self._session.execute(stmt)
