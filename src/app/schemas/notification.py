from datetime import datetime

from src.app.schemas.base import CamelModel
from src.app.schemas.user import AuthorInfo


class NotificationResponse(CamelModel):
    id: int
    user_id: str
    type: str
    title: str
    description: str
    is_read: bool
    payload: str | None = None
    action_status: str | None = None
    author_id: str | None = None
    author: AuthorInfo | None = None
    direction: str | None = None
    set_id: str | None = None
    set_title: str | None = None
    article_id: str | None = None
    article_title: str | None = None
    messages_count: int = 0
    created_at: datetime


class NotificationMessageResponse(CamelModel):
    id: int
    notification_id: int
    user_id: str | None = None
    author: AuthorInfo | None = None
    text: str
    created_at: datetime


class NotificationMessageCreate(CamelModel):
    text: str
