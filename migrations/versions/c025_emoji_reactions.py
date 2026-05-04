"""emoji reactions - allow multiple per user

Revision ID: c025_emoji_reactions
Revises: c024_uploads
Create Date: 2026-05-03 20:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c025_emoji_reactions"
down_revision: str | None = "c024_uploads"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("uq_reaction_per_user", "reactions", type_="unique")
    op.create_unique_constraint(
        "uq_reaction_per_user", "reactions", ["user_id", "target_type", "target_id", "type"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_reaction_per_user", "reactions", type_="unique")
    op.create_unique_constraint(
        "uq_reaction_per_user", "reactions", ["user_id", "target_type", "target_id"]
    )
