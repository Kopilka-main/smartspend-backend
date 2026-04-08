from datetime import date, datetime

from pydantic import Field

from src.app.schemas.base import CamelModel
from src.app.schemas.user import AuthorInfo


class ArticleBlockResponse(CamelModel):
    id: int
    position: int
    type: str
    text: str | None = None
    html: str | None = None
    items: list[str] | None = None
    title: str | None = None


class ArticleBlockCreate(CamelModel):
    position: int = Field(ge=0)
    type: str = Field(max_length=20)
    text: str | None = None
    html: str | None = None
    items: list[str] | None = None
    title: str | None = Field(None, max_length=200)


class ArticleResponse(CamelModel):
    id: str
    title: str
    article_type: str | None = None
    category_id: str | None = None
    preview: str | None = None
    published_at: date | None = None
    status: str
    views_count: int
    likes_count: int
    dislikes_count: int
    comments_count: int = 0
    linked_set_id: str | None = None
    linked_set_title: str | None = None
    blocks: list[ArticleBlockResponse] = []
    author: AuthorInfo | None = None
    created_at: datetime
    updated_at: datetime


class ArticleListItem(CamelModel):
    id: str
    title: str
    article_type: str | None = None
    category_id: str | None = None
    preview: str | None = None
    published_at: date | None = None
    status: str
    views_count: int
    likes_count: int
    dislikes_count: int
    comments_count: int = 0
    linked_set_id: str | None = None
    linked_set_title: str | None = None
    author: AuthorInfo | None = None
    created_at: datetime


class ArticleCreate(CamelModel):
    title: str = Field(min_length=1, max_length=300)
    article_type: str | None = Field(None, max_length=50)
    category_id: str | None = Field(None, max_length=20)
    preview: str | None = Field(None, max_length=2000)
    linked_set_id: str | None = None
    blocks: list[ArticleBlockCreate] = []


class ArticleUpdate(CamelModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    article_type: str | None = Field(None, max_length=50)
    category_id: str | None = Field(None, max_length=20)
    preview: str | None = Field(None, max_length=2000)
    linked_set_id: str | None = None
    blocks: list[ArticleBlockCreate] | None = None


class ArticleCommentResponse(CamelModel):
    id: int
    article_id: str
    user_id: str | None = None
    initials: str
    name: str
    text: str
    likes_count: int
    dislikes_count: int
    created_at: datetime


class ArticleCommentCreate(CamelModel):
    text: str = Field(min_length=1, max_length=2000)


class ArticleSetLinkCreate(CamelModel):
    set_id: str = Field(min_length=1, max_length=20)
