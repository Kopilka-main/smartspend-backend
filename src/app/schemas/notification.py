from datetime import datetime

from src.app.schemas.base import CamelModel


class NotificationResponse(CamelModel):
    id: int
    user_id: str
    type: str
    title: str
    description: str
    is_read: bool
    payload: str | None = None
    action_status: str | None = None
    created_at: datetime
