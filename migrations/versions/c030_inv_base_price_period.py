"""add base_price and period_years to inventory_items

Revision ID: c030_inv_base_period
Revises: c029_envelope_scale
Create Date: 2026-05-07 14:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c030_inv_base_period"
down_revision: str | None = "c029_envelope_scale"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("inventory_items", sa.Column("base_price", sa.Integer, nullable=True))
    op.add_column("inventory_items", sa.Column("period_years", sa.Numeric(10, 4), nullable=True))


def downgrade() -> None:
    op.drop_column("inventory_items", "period_years")
    op.drop_column("inventory_items", "base_price")
