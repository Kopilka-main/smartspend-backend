from datetime import date, datetime

from src.app.schemas.base import CamelModel
from src.app.schemas.user import AuthorInfo


class FeedItem(CamelModel):
    id: str
    type: str
    title: str
    preview: str | None = None
    category_id: str | None = None
    published_at: date | None = None
    created_at: datetime
    author: AuthorInfo | None = None

    # article-specific
    views_count: int | None = None
    likes_count: int | None = None
    dislikes_count: int | None = None
    article_type: str | None = None

    # set-specific
    items_count: int | None = None
    amount: int | None = None
    users_count: int | None = None
    source: str | None = None
    color: str | None = None
