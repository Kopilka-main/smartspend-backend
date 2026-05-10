"""set about md/html content

Revision ID: c039_set_about_content
Revises: c038_article_content
Create Date: 2026-05-11 01:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c039_set_about_content"
down_revision: str | None = "c038_article_content"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("sets", sa.Column("about_md", sa.Text, nullable=True))
    op.add_column("sets", sa.Column("about_html", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("sets", "about_html")
    op.drop_column("sets", "about_md")
