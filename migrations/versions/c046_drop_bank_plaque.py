"""drop bank_color / bank_text_color / bank_abbr from deposits and cards

Поля плашки-фолбэка банка больше не используются — у всех вкладов и карт есть логотип.

Revision ID: c046_drop_bank_plaque
Revises: c045_deposit_income_coef
Create Date: 2026-05-16 14:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c046_drop_bank_plaque"
down_revision: str | None = "c045_deposit_income_coef"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table in ("deposits", "cards"):
        op.drop_column(table, "bank_color")
        op.drop_column(table, "bank_text_color")
        op.drop_column(table, "bank_abbr")


def downgrade() -> None:
    for table in ("deposits", "cards"):
        op.add_column(table, sa.Column("bank_color", sa.String(length=7), nullable=False, server_default="#1B4F8A"))
        op.add_column(
            table, sa.Column("bank_text_color", sa.String(length=7), nullable=False, server_default="#FFF")
        )
        op.add_column(table, sa.Column("bank_abbr", sa.String(length=5), nullable=True))
