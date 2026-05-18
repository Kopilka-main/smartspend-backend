"""envelopes: добавить колонку paused

Статус паузы конверта теперь хранится отдельно от позиций инвентаря.
Конверт может быть активным, даже когда его позиции инвентаря на паузе
(позиции ждут заполнения и активируются по отдельности).

Revision ID: c048_envelope_paused
Revises: c047_article_set_link_multi
Create Date: 2026-05-17 13:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c048_envelope_paused"
down_revision: str | None = "c047_article_set_link_multi"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "envelopes",
        sa.Column("paused", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("envelopes", "paused")
