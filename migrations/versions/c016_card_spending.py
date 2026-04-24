"""move card spending to user_finance

Revision ID: c016_card_spending
Revises: c015_fix_cats
Create Date: 2026-04-24 17:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c016_card_spending"
down_revision: Union[str, None] = "c015_fix_cats"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_finance", sa.Column("card_spending", sa.dialects.postgresql.JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("user_finance", "card_spending")
