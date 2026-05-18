"""deposit ear

Revision ID: c042_deposit_ear
Revises: c041_deposit_bank_logo
Create Date: 2026-05-15 14:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c042_deposit_ear"
down_revision: str | None = "c041_deposit_bank_logo"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("deposits", sa.Column("ear", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("deposits", "ear")
