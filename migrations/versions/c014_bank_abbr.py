"""add bank_abbr to cards and deposits

Revision ID: c014_bank_abbr
Revises: c013_user_settings
Create Date: 2026-04-24 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c014_bank_abbr"
down_revision: Union[str, None] = "c013_user_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BANK_ABBRS = {
    "Т-Банк": "ТБ",
    "Альфа-Банк": "АБ",
    "Сбер": "Сб",
    "ВТБ": "ВТ",
    "Газпромбанк": "ГП",
    "Банк Дом.РФ": "ДР",
    "МТС Банк": "МТ",
    "Росбанк": "РБ",
    "Совкомбанк": "СК",
}


def upgrade() -> None:
    op.add_column("cards", sa.Column("bank_abbr", sa.String(5), nullable=True))
    op.add_column("deposits", sa.Column("bank_abbr", sa.String(5), nullable=True))

    conn = op.get_bind()
    for bank, abbr in BANK_ABBRS.items():
        conn.execute(
            sa.text("UPDATE cards SET bank_abbr = :abbr WHERE bank_name = :bank"),
            {"abbr": abbr, "bank": bank},
        )
        conn.execute(
            sa.text("UPDATE deposits SET bank_abbr = :abbr WHERE bank_name = :bank"),
            {"abbr": abbr, "bank": bank},
        )


def downgrade() -> None:
    op.drop_column("deposits", "bank_abbr")
    op.drop_column("cards", "bank_abbr")
