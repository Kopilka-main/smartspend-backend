"""add tariff to deposits, seed tariff data

Revision ID: c017_deposit_tariff
Revises: c016_card_spending
Create Date: 2026-04-26 02:00:00.000000
"""

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c017_deposit_tariff"
down_revision: Union[str, None] = "c016_card_spending"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TARIFFS = {
    "d7": {
        "name": "Инвестиционный / страховой продукт МТС",
        "cost": "от 50 000 руб единовременно",
        "conditions": "Необходимо оформить инвестиционный или накопительный страховой продукт МТС Банка одновременно с открытием вклада.",
        "benefits": ["Повышенная ставка на весь срок вклада", "Страховое покрытие жизни или капитала", "Потенциальный доход от инвест. инструмента"],
        "url": "https://www.mtsbank.ru/vklady/",
    },
    "d10": {
        "name": "Т-Привилегия / Т-Прайм",
        "cost": "от 199 руб/мес (или бесплатно)",
        "conditions": "Бесплатно при остатке от 100 000 руб или тратах от 30 000 руб/мес. Иначе 199 руб/мес.",
        "benefits": ["Кешбэк до 5% на все покупки", "Бесплатные переводы и снятие наличных", "Страховка при путешествиях за рубеж", "Приоритетная поддержка 24/7", "Консьерж-сервис (Т-Прайм)"],
        "url": "https://www.tbank.ru/privilege/",
    },
}


def upgrade() -> None:
    op.add_column("deposits", sa.Column("tariff", sa.dialects.postgresql.JSONB, nullable=True))
    conn = op.get_bind()
    for dep_id, tariff in TARIFFS.items():
        conn.execute(
            sa.text("UPDATE deposits SET tariff = CAST(:tariff AS jsonb) WHERE id = :id"),
            {"id": dep_id, "tariff": json.dumps(tariff, ensure_ascii=False)},
        )


def downgrade() -> None:
    op.drop_column("deposits", "tariff")
