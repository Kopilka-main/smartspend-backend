"""extend_set_items_for_frontend

Revision ID: fc5f79f67b0f
Revises: c001_seed_ref
Create Date: 2026-04-03 13:43:41.920342
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'fc5f79f67b0f'
down_revision: Union[str, None] = 'c001_seed_ref'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('set_items', sa.Column('price', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('set_items', sa.Column('daily_use', sa.Numeric(10, 2), nullable=True))
    op.add_column('set_items', sa.Column('wear_life_weeks', sa.Integer(), nullable=True))
    op.add_column('set_items', sa.Column('purchase_date', sa.Date(), nullable=True))
    op.add_column('set_items', sa.Column('planned_price', sa.Integer(), nullable=True))

    op.alter_column('set_items', 'qty', nullable=True)
    op.alter_column('set_items', 'unit', nullable=True)
    op.alter_column('set_items', 'base_price', nullable=True)
    op.alter_column('set_items', 'period_years', nullable=True)

    op.execute("UPDATE set_items SET price = COALESCE(base_price::integer, 0) WHERE price IS NULL")
    op.alter_column('set_items', 'price', server_default=None, nullable=False)


def downgrade() -> None:
    op.drop_column('set_items', 'planned_price')
    op.drop_column('set_items', 'purchase_date')
    op.drop_column('set_items', 'wear_life_weeks')
    op.drop_column('set_items', 'daily_use')
    op.drop_column('set_items', 'price')

    op.alter_column('set_items', 'qty', nullable=False)
    op.alter_column('set_items', 'unit', nullable=False)
    op.alter_column('set_items', 'base_price', nullable=False)
    op.alter_column('set_items', 'period_years', nullable=False)
