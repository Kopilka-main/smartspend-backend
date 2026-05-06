"""add scale to envelope

Revision ID: c029_envelope_scale
Revises: c028_ss_username
Create Date: 2026-05-06 22:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c029_envelope_scale"
down_revision: str | None = "c028_ss_username"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "envelopes",
        sa.Column("scale", sa.Numeric(6, 2), nullable=False, server_default="1.00"),
    )


def downgrade() -> None:
    op.drop_column("envelopes", "scale")
