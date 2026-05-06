"""set username for smartspend system user

Revision ID: c028_ss_username
Revises: c027_ss_sets_author
Create Date: 2026-05-06 15:30:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c028_ss_username"
down_revision: str | None = "c027_ss_sets_author"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


SS_USER_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    op.execute(
        f"""
        UPDATE users
        SET username = 'smartspend'
        WHERE id = '{SS_USER_ID}' AND username IS NULL
        """
    )


def downgrade() -> None:
    op.execute(
        f"""
        UPDATE users
        SET username = NULL
        WHERE id = '{SS_USER_ID}' AND username = 'smartspend'
        """
    )
