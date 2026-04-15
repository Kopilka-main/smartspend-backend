"""frontend requests: comment replies, set photos, set draft status

Revision ID: c006_frontend
Revises: c005_reads
Create Date: 2026-04-16 02:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c006_frontend"
down_revision: Union[str, None] = "c005_reads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("set_comments", sa.Column("parent_id", sa.Integer, sa.ForeignKey("set_comments.id", ondelete="CASCADE"), nullable=True))
    op.add_column("article_comments", sa.Column("parent_id", sa.Integer, sa.ForeignKey("article_comments.id", ondelete="CASCADE"), nullable=True))

    op.create_table(
        "set_photos",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("set_id", sa.String(20), sa.ForeignKey("sets.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("position", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.add_column("sets", sa.Column("status", sa.String(20), nullable=False, server_default="published"))
    op.add_column("sets", sa.Column("period", sa.String(50), nullable=True))
    op.add_column("sets", sa.Column("full_cost", sa.Integer, nullable=True))
    op.add_column("sets", sa.Column("monthly", sa.Integer, nullable=True))


def downgrade() -> None:
    op.drop_column("sets", "monthly")
    op.drop_column("sets", "full_cost")
    op.drop_column("sets", "period")
    op.drop_column("sets", "status")
    op.drop_table("set_photos")
    op.drop_column("article_comments", "parent_id")
    op.drop_column("set_comments", "parent_id")
