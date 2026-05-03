from fastapi import APIRouter, UploadFile

from src.app.core.dependencies import CurrentUser, Session
from src.app.schemas.base import ApiResponse
from src.app.schemas.upload import UploadResponse
from src.app.services.upload import UploadService

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("", response_model=ApiResponse[UploadResponse], status_code=201)
async def upload_file(file: UploadFile, user: CurrentUser, session: Session):
    service = UploadService(session)
    result = await service.upload(user.id, file)
    return ApiResponse(data=result)


@router.delete("/{upload_id}", response_model=ApiResponse[None])
async def delete_upload(upload_id: int, user: CurrentUser, session: Session):
    service = UploadService(session)
    await service.delete(upload_id, user.id)
    return ApiResponse(data=None)
