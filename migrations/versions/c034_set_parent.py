"""set parent link for user copies

Revision ID: c034_set_parent
Revises: c033_oauth_primary
Create Date: 2026-05-08 14:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c034_set_parent"
down_revision: str | None = "c033_oauth_primary"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sets",
        sa.Column("parent_set_id", sa.String(20), sa.ForeignKey("sets.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_sets_parent_set_id", "sets", ["parent_set_id"])


def downgrade() -> None:
    op.drop_index("ix_sets_parent_set_id", table_name="sets")
    op.drop_column("sets", "parent_set_id")
