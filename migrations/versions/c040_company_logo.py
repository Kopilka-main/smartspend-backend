"""company logo_url

Revision ID: c040_company_logo
Revises: c039_set_about_content
Create Date: 2026-05-15 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c040_company_logo"
down_revision: str | None = "c039_set_about_content"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("logo_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "logo_url")
