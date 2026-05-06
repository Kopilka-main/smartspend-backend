"""assign smartspend author to ss_* sets

Revision ID: c027_ss_sets_author
Revises: c026_rework_inv_groups
Create Date: 2026-05-06 13:40:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c027_ss_sets_author"
down_revision: str | None = "c026_rework_inv_groups"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


SS_AUTHOR_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    op.execute(
        f"""
        UPDATE sets
        SET author_id = '{SS_AUTHOR_ID}'
        WHERE source = 'smartspend' AND author_id IS NULL
        """
    )


def downgrade() -> None:
    op.execute(
        f"""
        UPDATE sets
        SET author_id = NULL
        WHERE source = 'smartspend' AND author_id = '{SS_AUTHOR_ID}'
        """
    )
