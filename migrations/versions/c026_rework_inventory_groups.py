"""rework inventory groups to match prototype

Revision ID: c026_rework_inv_groups
Revises: c025_emoji_reactions
Create Date: 2026-05-04 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c026_rework_inv_groups"
down_revision: str | None = "c025_emoji_reactions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


NEW_GROUPS = [
    ("g1", "Одежда и Обувь", "#B8A0C8"),
    ("g2", "Еда и Супермаркеты", "#8DBFA8"),
    ("g3", "Дом и Техника", "#9EA8C0"),
    ("g4", "Красота и Здоровье", "#C4B0C0"),
    ("g5", "Авто и Транспорт", "#8AAFC8"),
    ("g6", "Развлечения и Хобби", "#C8A8A0"),
    ("g7", "Образование и Дети", "#A8C0B0"),
    ("g8", "Прочие расходы", "#B0A898"),
]

NEW_GROUP_CATEGORIES = [
    ("g1", "clothes"),
    ("g2", "food"),
    ("g2", "cafe"),
    ("g3", "home"),
    ("g4", "beauty"),
    ("g5", "auto"),
    ("g6", "fun"),
    ("g6", "travel"),
    ("g7", "edu"),
    ("g8", "other"),
]

OLD_TO_NEW = {
    "food": "g2",
    "home": "g3",
    "cloth": "g1",
    "tech": "g3",
    "care": "g4",
    "other": "g8",
}


def upgrade() -> None:
    groups_table = sa.table(
        "inventory_groups",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("color", sa.String),
    )
    op.bulk_insert(groups_table, [{"id": g[0], "name": g[1], "color": g[2]} for g in NEW_GROUPS])

    for old, new in OLD_TO_NEW.items():
        op.execute(f"UPDATE inventory_items SET group_id = '{new}' WHERE group_id = '{old}'")

    op.execute("DELETE FROM inventory_group_categories WHERE group_id IN ('food','home','cloth','tech','care','other')")
    op.execute("DELETE FROM inventory_groups WHERE id IN ('food','home','cloth','tech','care','other')")

    gc_table = sa.table(
        "inventory_group_categories",
        sa.column("group_id", sa.String),
        sa.column("category_id", sa.String),
    )
    op.bulk_insert(gc_table, [{"group_id": gc[0], "category_id": gc[1]} for gc in NEW_GROUP_CATEGORIES])


def downgrade() -> None:
    reverse_map = {
        "g1": "cloth",
        "g2": "food",
        "g3": "home",
        "g4": "care",
        "g5": "other",
        "g6": "other",
        "g7": "other",
        "g8": "other",
    }

    old_groups = [
        ("food", "Еда", "#4CAF50"),
        ("home", "Дом", "#795548"),
        ("cloth", "Одежда", "#E91E63"),
        ("tech", "Техника", "#607D8B"),
        ("care", "Уход", "#F44336"),
        ("other", "Прочее", "#9E9E9E"),
    ]
    old_group_cats = [
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

    groups_table = sa.table(
        "inventory_groups",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("color", sa.String),
    )
    op.bulk_insert(groups_table, [{"id": g[0], "name": g[1], "color": g[2]} for g in old_groups])

    for new, old in reverse_map.items():
        op.execute(f"UPDATE inventory_items SET group_id = '{old}' WHERE group_id = '{new}'")

    op.execute("DELETE FROM inventory_group_categories WHERE group_id IN ('g1','g2','g3','g4','g5','g6','g7','g8')")
    op.execute("DELETE FROM inventory_groups WHERE id IN ('g1','g2','g3','g4','g5','g6','g7','g8')")

    gc_table = sa.table(
        "inventory_group_categories",
        sa.column("group_id", sa.String),
        sa.column("category_id", sa.String),
    )
    op.bulk_insert(gc_table, [{"group_id": gc[0], "category_id": gc[1]} for gc in old_group_cats])
