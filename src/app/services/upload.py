import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.upload import Upload
from src.app.schemas.upload import UploadResponse

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE = 5 * 1024 * 1024
UPLOAD_DIR = Path("/app/uploads/files")


class UploadService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upload(self, user_id: uuid.UUID, file: UploadFile) -> UploadResponse:
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type")

        content = await file.read()
        if len(content) > MAX_SIZE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 5 MB)")

        ext = Path(file.filename or "photo.jpg").suffix or ".jpg"
        unique_name = f"{user_id}_{int(time.time() * 1000)}{ext}"
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(UPLOAD_DIR / unique_name, "wb") as f:
            await f.write(content)

        url = f"/uploads/files/{unique_name}"
        upload = Upload(user_id=user_id, url=url, file_name=file.filename or unique_name)
        self._session.add(upload)
        await self._session.flush()
        await self._session.refresh(upload)
        await self._session.commit()
        return UploadResponse(
            id=upload.id,
            url=upload.url,
            file_name=upload.file_name,
            position=upload.position,
            created_at=upload.created_at,
        )

    async def delete(self, upload_id: int, user_id: uuid.UUID) -> None:
        upload = await self._session.get(Upload, upload_id)
        if upload is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")
        if upload.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your upload")
        if upload.linked_at is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete linked upload")
        file_path = Path("/app") / upload.url.lstrip("/")
        if file_path.exists():
            file_path.unlink()
        await self._session.delete(upload)
        await self._session.commit()

    async def link_uploads(
        self, upload_ids: list[int], user_id: uuid.UUID, entity_type: str, entity_id: str
    ) -> list[Upload]:
        if not upload_ids:
            return []
        stmt = select(Upload).where(
            Upload.id.in_(upload_ids),
            Upload.user_id == user_id,
            Upload.linked_at.is_(None),
        )
        result = await self._session.execute(stmt)
        uploads = list(result.scalars().all())
        if not uploads:
            return []
        now = datetime.now(UTC)
        ids = [u.id for u in uploads]
        await self._session.execute(
            sa_update(Upload)
            .where(Upload.id.in_(ids))
            .values(entity_type=entity_type, entity_id=entity_id, linked_at=now)
        )
        return uploads

    async def cleanup_stale(self, max_age_hours: int = 24) -> int:
        cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
        stmt = select(Upload).where(Upload.linked_at.is_(None), Upload.created_at < cutoff)
        result = await self._session.execute(stmt)
        stale = list(result.scalars().all())
        count = 0
        for u in stale:
            file_path = Path("/app") / u.url.lstrip("/")
            if file_path.exists():
                file_path.unlink()
            await self._session.delete(u)
            count += 1
        if count:
            await self._session.commit()
        return count
