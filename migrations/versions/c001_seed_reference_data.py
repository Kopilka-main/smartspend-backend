"""seed reference data

Revision ID: c001_seed_ref
Revises: b66e65d9221b
Create Date: 2026-04-02 22:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c001_seed_ref"
down_revision: Union[str, None] = "b66e65d9221b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CATEGORIES = [
    ("other", "Прочие расходы", "#9E9E9E"),
    ("food", "Еда и Супермаркеты", "#4CAF50"),
    ("cafe", "Кафе, Бары, Рестораны", "#FF9800"),
    ("auto", "Авто и Транспорт", "#2196F3"),
    ("home", "Дом и Техника", "#795548"),
    ("clothes", "Одежда и Обувь", "#E91E63"),
    ("fun", "Развлечения и Хобби", "#9C27B0"),
    ("beauty", "Красота и Здоровье", "#F44336"),
    ("edu", "Образование и Дети", "#3F51B5"),
    ("travel", "Путешествия и Отдых", "#00BCD4"),
]

GROUPS = [
    ("food", "Еда", "#4CAF50"),
    ("home", "Дом", "#795548"),
    ("cloth", "Одежда", "#E91E63"),
    ("tech", "Техника", "#607D8B"),
    ("care", "Уход", "#F44336"),
    ("other", "Прочее", "#9E9E9E"),
]

GROUP_CATEGORIES = [
    ("food", "food"),
    ("food", "cafe"),
    ("home", "home"),
    ("cloth", "clothes"),
    ("tech", "home"),
    ("care", "beauty"),
    ("other", "other"),
    ("other", "fun"),
    ("other", "auto"),
    ("other", "edu"),
    ("other", "travel"),
]


def upgrade() -> None:
    """Insert seed reference data."""
    cats_table = sa.table(
        "envelope_categories",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("color", sa.String),
    )
    op.bulk_insert(cats_table, [{"id": c[0], "name": c[1], "color": c[2]} for c in CATEGORIES])

    groups_table = sa.table(
        "inventory_groups",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("color", sa.String),
    )
    op.bulk_insert(groups_table, [{"id": g[0], "name": g[1], "color": g[2]} for g in GROUPS])

    gc_table = sa.table(
        "inventory_group_categories",
        sa.column("group_id", sa.String),
        sa.column("category_id", sa.String),
    )
    op.bulk_insert(gc_table, [{"group_id": gc[0], "category_id": gc[1]} for gc in GROUP_CATEGORIES])


def downgrade() -> None:
    """Remove seed reference data."""
    op.execute("DELETE FROM inventory_group_categories")
    op.execute("DELETE FROM inventory_groups")
    op.execute("DELETE FROM envelope_categories")
