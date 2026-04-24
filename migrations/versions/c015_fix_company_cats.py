"""fix company and promo category_ids to match envelope_categories

Revision ID: c015_fix_cats
Revises: c014_bank_abbr
Create Date: 2026-04-24 17:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c015_fix_cats"
down_revision: Union[str, None] = "c014_bank_abbr"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

REMAP = {
    "transport": "auto",
    "leisure": "fun",
    "health": "beauty",
    "education": "edu",
}


def upgrade() -> None:
    conn = op.get_bind()
    for old, new in REMAP.items():
        conn.execute(
            sa.text("UPDATE companies SET category_id = :new WHERE category_id = :old"),
            {"old": old, "new": new},
        )
        conn.execute(
            sa.text("UPDATE promos SET category_id = :new WHERE category_id = :old"),
            {"old": old, "new": new},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for old, new in REMAP.items():
        conn.execute(
            sa.text("UPDATE companies SET category_id = :old WHERE category_id = :new"),
            {"old": old, "new": new},
        )
        conn.execute(
            sa.text("UPDATE promos SET category_id = :old WHERE category_id = :new"),
            {"old": old, "new": new},
        )
