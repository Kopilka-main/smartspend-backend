"""deposit bank_logo_url

Revision ID: c041_deposit_bank_logo
Revises: c040_company_logo
Create Date: 2026-05-15 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c041_deposit_bank_logo"
down_revision: str | None = "c040_company_logo"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("deposits", sa.Column("bank_logo_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("deposits", "bank_logo_url")
