"""set notes

Revision ID: c023_set_notes
Revises: c023_oauth_fields
Create Date: 2026-05-02 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c023_set_notes"
down_revision: str | None = "c023_oauth_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "set_notes",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("set_id", sa.String(20), sa.ForeignKey("sets.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("set_notes")
