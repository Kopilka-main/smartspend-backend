"""relax inventory check constraints for new fields

Revision ID: c022_relax_constraints
Revises: c021_inventory_fields
Create Date: 2026-05-01 13:00:00.000000
"""

from typing import Sequence, Union

from alembic import op

revision: str = "c022_relax_constraints"
down_revision: Union[str, None] = "c021_inventory_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("chk_consumable", "inventory_items", type_="check")
    op.drop_constraint("chk_wear", "inventory_items", type_="check")


def downgrade() -> None:
    pass
