"""article notes for private articles

Revision ID: c008_notes
Revises: c007_batch
Create Date: 2026-04-21 15:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c008_notes"
down_revision: Union[str, None] = "c007_batch"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "article_notes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("article_id", sa.String(20), sa.ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("article_notes")
