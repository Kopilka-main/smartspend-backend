"""deposit income_coef

Revision ID: c045_deposit_income_coef
Revises: c044_promo_partner_company
Create Date: 2026-05-16 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c045_deposit_income_coef"
down_revision: str | None = "c044_promo_partner_company"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("deposits", sa.Column("income_coef", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("deposits", "income_coef")
