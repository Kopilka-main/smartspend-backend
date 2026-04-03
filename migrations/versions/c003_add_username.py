"""add username to users

Revision ID: c003_username
Revises: c002_seed_sets
Create Date: 2026-04-03 18:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c003_username"
down_revision: Union[str, None] = "c002_seed_sets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add username column to users table."""
    op.add_column("users", sa.Column("username", sa.String(50), nullable=True))
    op.create_index("ix_users_username", "users", ["username"], unique=True)


def downgrade() -> None:
    """Remove username column from users table."""
    op.drop_index("ix_users_username", table_name="users")
    op.drop_column("users", "username")
