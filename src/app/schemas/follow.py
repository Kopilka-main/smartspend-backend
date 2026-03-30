import uuid
from datetime import datetime

from src.app.schemas.base import CamelModel


class FollowResponse(CamelModel):
    follower_id: uuid.UUID
    following_id: uuid.UUID
    created_at: datetime
