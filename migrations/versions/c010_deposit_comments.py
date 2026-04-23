"""deposit comments

Revision ID: c010_deposit_comments
Revises: c009_kopilka
Create Date: 2026-04-23 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c010_deposit_comments"
down_revision: Union[str, None] = "c009_kopilka"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "deposit_comments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "deposit_id",
            sa.String(20),
            sa.ForeignKey("deposits.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("initials", sa.String(2), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column(
            "parent_id",
            sa.Integer,
            sa.ForeignKey("deposit_comments.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("likes_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("dislikes_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("deposit_comments")
