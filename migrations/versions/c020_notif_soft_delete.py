"""add is_deleted to notifications

Revision ID: c020_notif_soft_delete
Revises: c019_fix_notif_seed
Create Date: 2026-04-30 13:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c020_notif_soft_delete"
down_revision: Union[str, None] = "c019_fix_notif_seed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("notifications", "is_deleted")
