"""card bank_logo_url

Revision ID: c043_card_bank_logo
Revises: c042_deposit_ear
Create Date: 2026-05-15 13:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c043_card_bank_logo"
down_revision: str | None = "c042_deposit_ear"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("cards", sa.Column("bank_logo_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("cards", "bank_logo_url")
