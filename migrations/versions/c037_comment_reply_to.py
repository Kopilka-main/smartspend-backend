"""comment reply_to for nested replies

Revision ID: c037_comment_reply_to
Revises: c036_article_bookmarks
Create Date: 2026-05-10 22:40:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c037_comment_reply_to"
down_revision: str | None = "c036_article_bookmarks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "article_comments",
        sa.Column(
            "reply_to_id",
            sa.Integer,
            sa.ForeignKey("article_comments.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "set_comments",
        sa.Column(
            "reply_to_id",
            sa.Integer,
            sa.ForeignKey("set_comments.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "promo_comments",
        sa.Column(
            "reply_to_id",
            sa.Integer,
            sa.ForeignKey("promo_comments.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "deposit_comments",
        sa.Column(
            "reply_to_id",
            sa.Integer,
            sa.ForeignKey("deposit_comments.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("deposit_comments", "reply_to_id")
    op.drop_column("promo_comments", "reply_to_id")
    op.drop_column("set_comments", "reply_to_id")
    op.drop_column("article_comments", "reply_to_id")
