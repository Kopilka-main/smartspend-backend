from datetime import datetime

from src.app.schemas.base import CamelModel


class UploadResponse(CamelModel):
    id: int
    url: str
    file_name: str
    position: int = 0
    created_at: datetime
