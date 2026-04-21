import time
import uuid
from datetime import date

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.article import Article, ArticleBlock
from src.app.models.article_comment import ArticleComment
from src.app.models.article_photo import ArticlePhoto
from src.app.models.article_read import ArticleRead
from src.app.models.article_set_link import ArticleSetLink
from src.app.models.set import Set
from src.app.models.user import User
from src.app.repositories.article import ArticleRepository
from src.app.schemas.article import (
    ArticleBlockResponse,
    ArticleCommentCreate,
    ArticleCommentResponse,
    ArticleCreate,
    ArticleListItem,
    ArticlePhotoResponse,
    ArticleResponse,
    ArticleSetLinkCreate,
    ArticleUpdate,
)
from src.app.schemas.user import AuthorInfo


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
        initials=user.initials,
        color=user.color,
        avatar_url=user.avatar_url,
    )


def _article_to_response(
    a: Article,
    set_title: str | None = None,
    category_name: str | None = None,
    linked_sets: list | None = None,
    set_link=None,
) -> ArticleResponse:
    from src.app.schemas.article import ArticlePhotoResponse

    photos = [
        ArticlePhotoResponse(id=p.id, url=p.url, file_name=p.file_name, position=p.position, created_at=p.created_at)
        for p in (a.photos or [])
    ]
    return ArticleResponse(
        id=a.id,
        title=a.title,
        article_type=a.article_type,
        category_id=a.category_id,
        category_name=category_name,
        preview=a.preview,
        published_at=a.published_at,
        status=a.status,
        is_private=a.is_private,
        read_time=a.read_time,
        tags=a.tags,
        views_count=a.views_count,
        likes_count=a.likes_count,
        dislikes_count=a.dislikes_count,
        comments_count=len(a.comments) if a.comments else 0,
        linked_set_id=a.linked_set_id,
        linked_set_ids=a.linked_set_ids,
        linked_set_title=set_title,
        linked_sets=linked_sets or [],
        set_link=set_link,
        blocks=[],
        photos=photos,
        author=_author_info(a.author),
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


def _article_to_list_item(
    a: Article,
    set_title: str | None = None,
    category_name: str | None = None,
    linked_sets: list | None = None,
    set_link=None,
) -> ArticleListItem:
    return ArticleListItem(
        id=a.id,
        title=a.title,
        article_type=a.article_type,
        category_id=a.category_id,
        category_name=category_name,
        preview=a.preview,
        published_at=a.published_at,
        status=a.status,
        is_private=a.is_private,
        read_time=a.read_time,
        tags=a.tags,
        views_count=a.views_count,
        likes_count=a.likes_count,
        dislikes_count=a.dislikes_count,
        comments_count=len(a.comments) if a.comments else 0,
        linked_set_id=a.linked_set_id,
        linked_set_ids=a.linked_set_ids,
        linked_set_title=set_title,
        linked_sets=linked_sets or [],
        author=_author_info(a.author),
        created_at=a.created_at,
    )


class ArticleService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ArticleRepository(session)

    async def _resolve_sets_and_cats(self, articles: list[Article]):
        from src.app.models.envelope_category import EnvelopeCategory
        from src.app.schemas.article import LinkedSetInfo

        all_set_ids: set[str] = set()
        cat_ids: set[str] = set()
        for a in articles:
            if a.linked_set_id:
                all_set_ids.add(a.linked_set_id)
            for sid in a.linked_set_ids or []:
                all_set_ids.add(sid)
            if a.category_id:
                cat_ids.add(a.category_id)

        sets_raw: dict[str, dict] = {}
        if all_set_ids:
            stmt = select(
                Set.id,
                Set.title,
                Set.color,
                Set.category_id,
                Set.description,
                Set.amount,
                Set.amount_label,
                Set.period,
                Set.users_count,
            ).where(Set.id.in_(all_set_ids))
            for row in (await self._session.execute(stmt)).all():
                sets_raw[row[0]] = {
                    "id": row[0],
                    "title": row[1],
                    "color": row[2],
                    "category_id": row[3],
                    "description": row[4],
                    "amount": row[5],
                    "amount_label": row[6],
                    "period": row[7],
                    "users_count": row[8] or 0,
                }

        cats_map: dict[str, str] = {}
        all_cat_ids = cat_ids | {s["category_id"] for s in sets_raw.values() if s.get("category_id")}
        if all_cat_ids:
            stmt = select(EnvelopeCategory.id, EnvelopeCategory.name).where(EnvelopeCategory.id.in_(all_cat_ids))
            cats_map = dict((await self._session.execute(stmt)).all())

        sets_map: dict[str, LinkedSetInfo] = {}
        for sid, s in sets_raw.items():
            sets_map[sid] = LinkedSetInfo(
                id=s["id"],
                title=s["title"],
                color=s["color"],
                category_id=s["category_id"],
                category_name=cats_map.get(s["category_id"]),
                amount=s["amount"],
                period=s["period"],
            )

        return sets_map, sets_raw, cats_map

    async def _enrich_article(self, a, sets_map, sets_raw, cats_map):
        from src.app.schemas.article import SetLinkCard

        set_title = sets_map[a.linked_set_id].title if a.linked_set_id and a.linked_set_id in sets_map else None
        cat_name = cats_map.get(a.category_id) if a.category_id else None
        linked = [sets_map[sid] for sid in (a.linked_set_ids or []) if sid in sets_map]

        set_link = None
        if a.linked_set_id and a.linked_set_id in sets_raw:
            s = sets_raw[a.linked_set_id]
            set_link = SetLinkCard(
                id=s["id"],
                title=s["title"],
                description=s["description"],
                color=s["color"],
                amount=s["amount"],
                amount_label=s["amount_label"],
                period=s["period"],
                users_count=s["users_count"],
            )

        return set_title, cat_name, linked, set_link

    async def list_published(
        self,
        category_id: str | None = None,
        author_id: uuid.UUID | None = None,
        search: str | None = None,
        sort: str = "newest",
        limit: int = 20,
        offset: int = 0,
        linked_set_id: str | None = None,
    ) -> tuple[list[ArticleListItem], int]:
        articles, total = await self._repo.list_published(
            category_id=category_id,
            author_id=author_id,
            search=search,
            sort=sort,
            limit=limit,
            offset=offset,
            linked_set_id=linked_set_id,
        )
        sets_map, sets_raw, cats_map = await self._resolve_sets_and_cats(articles)
        result = []
        for a in articles:
            st, cn, ls, sl = await self._enrich_article(a, sets_map, sets_raw, cats_map)
            result.append(_article_to_list_item(a, set_title=st, category_name=cn, linked_sets=ls, set_link=sl))
        return result, total

    async def list_by_author(
        self, author_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> tuple[list[ArticleListItem], int]:
        articles, total = await self._repo.list_by_author(author_id, limit, offset)
        sets_map, sets_raw, cats_map = await self._resolve_sets_and_cats(articles)
        result = []
        for a in articles:
            st, cn, ls, sl = await self._enrich_article(a, sets_map, sets_raw, cats_map)
            result.append(_article_to_list_item(a, set_title=st, category_name=cn, linked_sets=ls, set_link=sl))
        return result, total

    async def get_article(self, article_id: str) -> ArticleResponse:
        a = await self._repo.get_by_id(article_id)
        if a is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
        sets_map, sets_raw, cats_map = await self._resolve_sets_and_cats([a])
        st, cn, ls, sl = await self._enrich_article(a, sets_map, sets_raw, cats_map)
        resp = _article_to_response(a, set_title=st, category_name=cn, linked_sets=ls, set_link=sl)
        resp.blocks = [
            ArticleBlockResponse(
                id=b.id,
                position=b.position,
                type=b.type,
                text=b.text,
                html=b.html,
                items=b.items,
                title=b.title,
            )
            for b in (a.blocks or [])
        ]
        return resp

    async def create_article(self, user: User, data: ArticleCreate) -> ArticleResponse:
        article_id = f"a_{int(time.time() * 1000)}"
        article = Article(
            id=article_id,
            author_id=user.id,
            title=data.title,
            article_type=data.article_type,
            category_id=data.category_id,
            preview=data.preview,
            is_private=data.is_private,
            read_time=data.read_time,
            tags=data.tags,
            linked_set_id=data.linked_set_id,
            linked_set_ids=data.linked_set_ids,
            status="draft",
        )
        await self._repo.create(article)

        if data.blocks:
            blocks = [
                ArticleBlock(
                    article_id=article_id,
                    position=b.position,
                    type=b.type,
                    text=b.text,
                    html=b.html,
                    items=b.items,
                    title=b.title,
                )
                for b in data.blocks
            ]
            await self._repo.add_blocks(blocks)

        await self._session.commit()
        self._session.expire_all()
        return await self.get_article(article_id)

    async def update_article(self, article_id: str, user: User, data: ArticleUpdate) -> ArticleResponse:
        a = await self._repo.get_by_id(article_id)
        if a is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
        if a.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your article")
        if a.status == "published":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Published articles cannot be edited",
            )

        updates: dict = {}
        if data.title is not None:
            updates["title"] = data.title
        if data.article_type is not None:
            updates["article_type"] = data.article_type
        if data.category_id is not None:
            updates["category_id"] = data.category_id
        if data.preview is not None:
            updates["preview"] = data.preview
        if data.linked_set_id is not None:
            updates["linked_set_id"] = data.linked_set_id

        if updates:
            stmt = sa_update(Article).where(Article.id == article_id).values(**updates)
            await self._session.execute(stmt)

        if data.blocks is not None:
            await self._repo.delete_blocks_by_article(article_id)
            blocks = [
                ArticleBlock(
                    article_id=article_id,
                    position=b.position,
                    type=b.type,
                    text=b.text,
                    html=b.html,
                    items=b.items,
                    title=b.title,
                )
                for b in data.blocks
            ]
            await self._repo.add_blocks(blocks)

        await self._session.commit()
        self._session.expire_all()
        return await self.get_article(article_id)

    async def publish_article(self, article_id: str, user: User) -> ArticleResponse:
        a = await self._repo.get_by_id(article_id)
        if a is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
        if a.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your article")
        if a.status == "published":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already published")

        stmt = (
            sa_update(Article)
            .where(Article.id == article_id)
            .values(
                status="published",
                published_at=date.today(),
            )
        )
        await self._session.execute(stmt)
        await self._session.commit()
        self._session.expire_all()
        return await self.get_article(article_id)

    async def delete_article(self, article_id: str, user: User) -> None:
        a = await self._repo.get_by_id(article_id)
        if a is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
        if a.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your article")
        await self._repo.delete_article(article_id)
        await self._session.commit()

    async def mark_read(self, article_id: str, user_id: uuid.UUID | None = None) -> None:
        a = await self._repo.get_by_id(article_id)
        if a is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
        stmt = sa_update(Article).where(Article.id == article_id).values(views_count=Article.views_count + 1)
        await self._session.execute(stmt)
        if user_id:
            existing = await self._session.execute(
                select(ArticleRead).where(ArticleRead.user_id == user_id, ArticleRead.article_id == article_id)
            )
            if not existing.scalar_one_or_none():
                self._session.add(ArticleRead(user_id=user_id, article_id=article_id))
        await self._session.commit()

    async def list_comments(
        self, article_id: str, sort: str = "new", limit: int = 50, offset: int = 0
    ) -> tuple[list[ArticleCommentResponse], int]:
        comments, total = await self._repo.list_comments(article_id, sort, limit, offset)
        return [
            ArticleCommentResponse(
                id=c.id,
                article_id=c.article_id,
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

    async def add_comment(self, article_id: str, user: User, data: ArticleCommentCreate) -> ArticleCommentResponse:
        a = await self._repo.get_by_id(article_id)
        if a is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

        comment = ArticleComment(
            article_id=article_id,
            user_id=user.id,
            initials=user.initials,
            name=user.display_name,
            text=data.text,
            parent_id=data.parent_id,
        )
        comment = await self._repo.add_comment(comment)
        await self._session.commit()
        return ArticleCommentResponse(
            id=comment.id,
            article_id=comment.article_id,
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

    async def link_to_set(self, article_id: str, user: User, data: ArticleSetLinkCreate) -> None:
        link = ArticleSetLink(
            article_id=article_id,
            user_id=user.id,
            set_id=data.set_id,
        )
        await self._repo.link_to_set(link)
        await self._session.commit()

    async def unlink_from_set(self, article_id: str, user: User) -> None:
        await self._repo.unlink_from_set(article_id, user.id)
        await self._session.commit()

    async def add_photo(self, article_id: str, user: User, file: UploadFile) -> ArticlePhotoResponse:
        from pathlib import Path

        import aiofiles

        a = await self._repo.get_by_id(article_id)
        if a is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
        if a.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your article")

        allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
        if file.content_type not in allowed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type")

        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 5 MB)")

        ext = Path(file.filename or "photo.jpg").suffix or ".jpg"
        unique_name = f"{article_id}_{int(time.time() * 1000)}{ext}"
        upload_dir = Path("/app/uploads/article_photos") / article_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(upload_dir / unique_name, "wb") as f:
            await f.write(content)

        url = f"/uploads/article_photos/{article_id}/{unique_name}"
        position = len(a.photos) if a.photos else 0
        photo = ArticlePhoto(article_id=article_id, url=url, file_name=file.filename or unique_name, position=position)
        self._session.add(photo)
        await self._session.flush()
        await self._session.refresh(photo)
        await self._session.commit()
        return ArticlePhotoResponse(
            id=photo.id, url=photo.url, file_name=photo.file_name, position=photo.position, created_at=photo.created_at
        )

    async def delete_photo(self, photo_id: int, user: User) -> None:
        from pathlib import Path

        photo = await self._session.get(ArticlePhoto, photo_id)
        if photo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
        a = await self._repo.get_by_id(photo.article_id)
        if a is None or a.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your article")
        file_path = Path("/app") / photo.url.lstrip("/")
        if file_path.exists():
            file_path.unlink()
        await self._session.delete(photo)
        await self._session.commit()

    async def add_note(self, article_id: str, user, text: str) -> dict:
        from src.app.models.article_note import ArticleNote

        if not text or not text.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text is required")
        note = ArticleNote(article_id=article_id, user_id=user.id, text=text.strip())
        self._session.add(note)
        await self._session.flush()
        await self._session.refresh(note)
        await self._session.commit()
        return {"id": note.id, "text": note.text, "createdAt": note.created_at.isoformat()}

    async def delete_note(self, note_id: int, user) -> None:
        from src.app.models.article_note import ArticleNote

        note = await self._session.get(ArticleNote, note_id)
        if note is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        if note.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your note")
        await self._session.delete(note)
        await self._session.commit()

    async def _get_notes(self, article_id: str, user_id) -> list:
        from src.app.models.article_note import ArticleNote

        stmt = (
            select(ArticleNote)
            .where(ArticleNote.article_id == article_id, ArticleNote.user_id == user_id)
            .order_by(ArticleNote.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [{"id": n.id, "text": n.text, "createdAt": n.created_at.isoformat()} for n in result.scalars().all()]
