"""article bookmarks

Revision ID: c036_article_bookmarks
Revises: c035_inventory_notes
Create Date: 2026-05-09 16:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c036_article_bookmarks"
down_revision: str | None = "c035_inventory_notes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "article_bookmarks",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "article_id",
            sa.String(20),
            sa.ForeignKey("articles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "article_id", name="uq_article_bookmark"),
    )


def downgrade() -> None:
    op.drop_table("article_bookmarks")
