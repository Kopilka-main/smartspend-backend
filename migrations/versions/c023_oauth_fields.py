"""add oauth_provider and oauth_id to users

Revision ID: c023_oauth_fields
Revises: c022_relax_constraints
Create Date: 2026-05-01 17:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c023_oauth_fields"
down_revision: Union[str, None] = "c022_relax_constraints"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("oauth_provider", sa.String(20), nullable=True))
    op.add_column("users", sa.Column("oauth_id", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "oauth_id")
    op.drop_column("users", "oauth_provider")
