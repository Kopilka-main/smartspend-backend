"""promo partner_company_id

Revision ID: c044_promo_partner_company
Revises: c043_card_bank_logo
Create Date: 2026-05-15 15:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c044_promo_partner_company"
down_revision: str | None = "c043_card_bank_logo"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("promos", sa.Column("partner_company_id", sa.String(length=30), nullable=True))
    op.create_foreign_key(
        "fk_promos_partner_company_id",
        "promos",
        "companies",
        ["partner_company_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_promos_partner_company_id", "promos", type_="foreignkey")
    op.drop_column("promos", "partner_company_id")
