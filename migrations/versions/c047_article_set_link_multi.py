"""article_set_links: расширить первичный ключ до (article_id, user_id, set_id)

Раньше PK был (article_id, user_id) — пользователь мог прикрепить статью
лишь к одному набору. Теперь одну статью можно прикреплять к нескольким
своим наборам (личным и дочерним).

Revision ID: c047_article_set_link_multi
Revises: c046_drop_bank_plaque
Create Date: 2026-05-17 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c047_article_set_link_multi"
down_revision: str | None = "c046_drop_bank_plaque"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("article_set_links_pkey", "article_set_links", type_="primary")
    op.create_primary_key(
        "article_set_links_pkey",
        "article_set_links",
        ["article_id", "user_id", "set_id"],
    )


def downgrade() -> None:
    # Перед сужением PK убираем дубликаты (article_id, user_id), оставляя одну строку
    op.execute(
        """
        DELETE FROM article_set_links a
        USING article_set_links b
        WHERE a.ctid < b.ctid
          AND a.article_id = b.article_id
          AND a.user_id = b.user_id
        """
    )
    op.drop_constraint("article_set_links_pkey", "article_set_links", type_="primary")
    op.create_primary_key(
        "article_set_links_pkey",
        "article_set_links",
        ["article_id", "user_id"],
    )
