"""add title, code, source_url, promo_filter to promos

Revision ID: c011_promo_fields
Revises: c010_deposit_comments
Create Date: 2026-04-23 13:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c011_promo_fields"
down_revision: Union[str, None] = "c010_deposit_comments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("promos", sa.Column("title", sa.String(300), nullable=True))
    op.add_column("promos", sa.Column("code", sa.String(100), nullable=True))
    op.add_column("promos", sa.Column("source_url", sa.Text, nullable=True))
    op.add_column("promos", sa.Column("promo_filter", sa.String(30), nullable=True))


def downgrade() -> None:
    op.drop_column("promos", "promo_filter")
    op.drop_column("promos", "source_url")
    op.drop_column("promos", "code")
    op.drop_column("promos", "title")
