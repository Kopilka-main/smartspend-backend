from datetime import datetime

from pydantic import Field

from src.app.schemas.base import CamelModel


class ReactionCreate(CamelModel):
    target_type: str = Field(pattern="^(article|set|article_comment|set_comment)$")
    target_id: str = Field(max_length=30)
    type: str = Field(pattern="^(like|dislike)$")


class ReactionResponse(CamelModel):
    id: int
    user_id: str
    target_type: str
    target_id: str
    type: str
    created_at: datetime
