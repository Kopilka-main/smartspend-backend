"""add is_primary to user_oauth_links

Revision ID: c033_oauth_primary
Revises: c032_oauth_links
Create Date: 2026-05-08 00:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c033_oauth_primary"
down_revision: str | None = "c032_oauth_links"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_oauth_links",
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
    )
    op.execute(
        """
        UPDATE user_oauth_links l
        SET is_primary = TRUE
        FROM users u
        WHERE l.user_id = u.id
          AND u.password_hash = 'oauth'
          AND u.oauth_provider = l.provider
        """
    )


def downgrade() -> None:
    op.drop_column("user_oauth_links", "is_primary")
