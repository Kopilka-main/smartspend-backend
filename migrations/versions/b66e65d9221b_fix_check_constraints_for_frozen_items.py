"""fix_check_constraints_for_frozen_items

Revision ID: b66e65d9221b
Revises: 1eda53150f25
Create Date: 2026-03-31 00:58:37.648780
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b66e65d9221b'
down_revision: Union[str, None] = '1eda53150f25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('chk_consumable', 'inventory_items', type_='check')
    op.drop_constraint('chk_wear', 'inventory_items', type_='check')
    op.create_check_constraint(
        'chk_consumable', 'inventory_items',
        "paused = true OR type <> 'consumable' OR (qty IS NOT NULL AND daily_use IS NOT NULL AND last_bought IS NOT NULL)"
    )
    op.create_check_constraint(
        'chk_wear', 'inventory_items',
        "paused = true OR type <> 'wear' OR wear_life_weeks IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_constraint('chk_consumable', 'inventory_items', type_='check')
    op.drop_constraint('chk_wear', 'inventory_items', type_='check')
    op.create_check_constraint(
        'chk_consumable', 'inventory_items',
        "type <> 'consumable' OR (qty IS NOT NULL AND daily_use IS NOT NULL AND last_bought IS NOT NULL)"
    )
    op.create_check_constraint(
        'chk_wear', 'inventory_items',
        "type <> 'wear' OR wear_life_weeks IS NOT NULL"
    )
