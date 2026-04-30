"""add wear_life, wear_life_unit, use_rate, use_period to inventory_items

Revision ID: c021_inventory_fields
Revises: c020_notif_soft_delete
Create Date: 2026-05-01 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c021_inventory_fields"
down_revision: str | None = "c020_notif_soft_delete"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("inventory_items", sa.Column("wear_life", sa.Integer, nullable=True))
    op.add_column("inventory_items", sa.Column("wear_life_unit", sa.String(10), nullable=True))
    op.add_column("inventory_items", sa.Column("use_rate", sa.Numeric(10, 4), nullable=True))
    op.add_column("inventory_items", sa.Column("use_period", sa.String(10), nullable=True))


def downgrade() -> None:
    op.drop_column("inventory_items", "use_period")
    op.drop_column("inventory_items", "use_rate")
    op.drop_column("inventory_items", "wear_life_unit")
    op.drop_column("inventory_items", "wear_life")
