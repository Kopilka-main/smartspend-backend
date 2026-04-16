"""batch: set likes, article privacy/tags/readtime/photos, bookmarks, linked sets array

Revision ID: c007_batch
Revises: c006_frontend
Create Date: 2026-04-16 03:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c007_batch"
down_revision: Union[str, None] = "c006_frontend"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sets", sa.Column("likes_count", sa.Integer, nullable=False, server_default="0"))
    op.add_column("sets", sa.Column("dislikes_count", sa.Integer, nullable=False, server_default="0"))

    op.add_column("articles", sa.Column("is_private", sa.Boolean, nullable=False, server_default="false"))
    op.add_column("articles", sa.Column("read_time", sa.Integer, nullable=True))
    op.add_column("articles", sa.Column("tags", sa.ARRAY(sa.Text), nullable=True))
    op.add_column("articles", sa.Column("linked_set_ids", sa.ARRAY(sa.String(20)), nullable=True))

    op.create_table(
        "article_photos",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("article_id", sa.String(20), sa.ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("position", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "saved_sets",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("set_id", sa.String(20), sa.ForeignKey("sets.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "set_id", name="uq_saved_set"),
    )


def downgrade() -> None:
    op.drop_table("saved_sets")
    op.drop_table("article_photos")
    op.drop_column("articles", "linked_set_ids")
    op.drop_column("articles", "tags")
    op.drop_column("articles", "read_time")
    op.drop_column("articles", "is_private")
    op.drop_column("sets", "dislikes_count")
    op.drop_column("sets", "likes_count")
