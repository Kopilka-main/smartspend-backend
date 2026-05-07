"""oauth links table - multiple providers per user

Revision ID: c032_oauth_links
Revises: c031_oauth_states
Create Date: 2026-05-07 23:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c032_oauth_links"
down_revision: str | None = "c031_oauth_states"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_oauth_links",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("oauth_id", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("provider", "oauth_id", name="uq_oauth_provider_id"),
        sa.UniqueConstraint("user_id", "provider", name="uq_user_oauth_provider"),
    )
    op.execute(
        """
        INSERT INTO user_oauth_links (user_id, provider, oauth_id)
        SELECT id, oauth_provider, oauth_id
        FROM users
        WHERE oauth_provider IS NOT NULL AND oauth_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_table("user_oauth_links")
