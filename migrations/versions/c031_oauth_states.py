"""oauth states table

Revision ID: c031_oauth_states
Revises: c030_inv_base_period
Create Date: 2026-05-07 22:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c031_oauth_states"
down_revision: str | None = "c030_inv_base_period"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "oauth_states",
        sa.Column("state", sa.String(100), primary_key=True),
        sa.Column("verifier", sa.String(200), nullable=True),
        sa.Column("link_user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("oauth_states")
