"""article raw content fields (md/html)

Revision ID: c038_article_content
Revises: c037_comment_reply_to
Create Date: 2026-05-10 22:55:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c038_article_content"
down_revision: str | None = "c037_comment_reply_to"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("content_md", sa.Text, nullable=True))
    op.add_column("articles", sa.Column("content_html", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("articles", "content_html")
    op.drop_column("articles", "content_md")
