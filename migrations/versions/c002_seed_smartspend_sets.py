"""seed smartspend sets

Revision ID: c002_seed_sets
Revises: fc5f79f67b0f
Create Date: 2026-04-03 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import date

revision: str = "c002_seed_sets"
down_revision: Union[str, None] = "fc5f79f67b0f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SETS = [
    {
        "id": "ss_food_base",
        "source": "smartspend",
        "category_id": "food",
        "set_type": "base",
        "color": "#8DBFA8",
        "title": "Базовое питание",
        "description": "Полноценный рацион на месяц: крупы, овощи, белок, молочка, масло",
        "amount": 12000,
        "amount_label": "руб / месяц",
        "users_count": 18,
        "is_private": False,
        "hidden": False,
        "about_title": "Зачем этот набор",
        "about_text": "Минимальная продуктовая корзина для одного человека. Покрывает базовые потребности в питании без излишеств.",
    },
    {
        "id": "ss_home_chem",
        "source": "smartspend",
        "category_id": "home",
        "set_type": "base",
        "color": "#8DBFA8",
        "title": "Бытовая химия",
        "description": "Стирка, уборка, посуда — всё что нужно для чистоты дома",
        "amount": 2200,
        "amount_label": "руб / месяц",
        "users_count": 6,
        "is_private": False,
        "hidden": False,
        "about_title": None,
        "about_text": None,
    },
    {
        "id": "ss_cloth_base",
        "source": "smartspend",
        "category_id": "clothes",
        "set_type": "base",
        "color": "#8DBFA8",
        "title": "Базовый гардероб на сезон",
        "description": "Капсульный гардероб на год — то без чего невозможно обойтись",
        "amount": 42000,
        "amount_label": "руб / сезон",
        "users_count": 9,
        "is_private": False,
        "hidden": False,
        "about_title": None,
        "about_text": None,
    },
    {
        "id": "ss_food_snack",
        "source": "smartspend",
        "category_id": "food",
        "set_type": "custom",
        "color": "#C4A882",
        "title": "Вкусняшки и снеки",
        "description": "Сладкое, кофе, соки, снеки — всё что балует, но не обязательно",
        "amount": 3500,
        "amount_label": "руб / месяц",
        "users_count": 4,
        "is_private": False,
        "hidden": False,
        "about_title": None,
        "about_text": None,
    },
    {
        "id": "ss_auto_pub",
        "source": "smartspend",
        "category_id": "auto",
        "set_type": "base",
        "color": "#8DBFA8",
        "title": "Общественный транспорт",
        "description": "Ежемесячный проездной + такси на крайний случай",
        "amount": 3200,
        "amount_label": "руб / месяц",
        "users_count": 2,
        "is_private": False,
        "hidden": False,
        "about_title": None,
        "about_text": None,
    },
    {
        "id": "ss_care_base",
        "source": "smartspend",
        "category_id": "beauty",
        "set_type": "base",
        "color": "#8DBFA8",
        "title": "Забота о себе — базовый уход",
        "description": "Средства гигиены и ухода на каждый день",
        "amount": 4500,
        "amount_label": "руб / месяц",
        "users_count": 7,
        "is_private": False,
        "hidden": False,
        "about_title": None,
        "about_text": None,
    },
    {
        "id": "ss_fun_gifts",
        "source": "smartspend",
        "category_id": "fun",
        "set_type": "custom",
        "color": "#C4A882",
        "title": "Подарки близким",
        "description": "Откладываем весь год — тратим на дни рождения и праздники",
        "amount": 2000,
        "amount_label": "руб / месяц",
        "users_count": 3,
        "is_private": False,
        "hidden": False,
        "about_title": None,
        "about_text": None,
    },
    {
        "id": "ss_care_skin",
        "source": "community",
        "category_id": "beauty",
        "set_type": "custom",
        "color": "#C4A882",
        "title": "Уход за кожей",
        "description": "Базовый корейский уход: очищение, тонер, крем, SPF",
        "amount": 5500,
        "amount_label": "руб / месяц",
        "users_count": 5,
        "is_private": False,
        "hidden": False,
        "about_title": None,
        "about_text": None,
    },
    {
        "id": "ss_cloth_sport",
        "source": "community",
        "category_id": "clothes",
        "set_type": "custom",
        "color": "#C4A882",
        "title": "Спортивная одежда",
        "description": "Для тренировок и активного отдыха: зал, бег, велопрогулки",
        "amount": 18000,
        "amount_label": "руб / сезон",
        "users_count": 2,
        "is_private": False,
        "hidden": False,
        "about_title": None,
        "about_text": None,
    },
]

ITEMS = {
    "ss_food_base": [
        {"name": "Крупы", "item_type": "consumable", "price": 200, "qty": 3, "unit": "кг", "daily_use": 0.1, "base_price": 200, "period_years": 0.0833},
        {"name": "Овощи и фрукты", "item_type": "consumable", "price": 500, "qty": 5, "unit": "кг", "daily_use": 0.5, "base_price": 500, "period_years": 0.0833},
        {"name": "Мясо и рыба", "item_type": "consumable", "price": 800, "qty": 3, "unit": "кг", "daily_use": 0.2, "base_price": 800, "period_years": 0.0833},
        {"name": "Молочные продукты", "item_type": "consumable", "price": 300, "qty": 5, "unit": "л", "daily_use": 0.3, "base_price": 300, "period_years": 0.0833},
        {"name": "Масло и приправы", "item_type": "consumable", "price": 400, "qty": 1, "unit": "л", "daily_use": 0.03, "base_price": 400, "period_years": 0.25},
        {"name": "Хлеб и выпечка", "item_type": "consumable", "price": 60, "qty": 1, "unit": "шт", "daily_use": 0.5, "base_price": 60, "period_years": 0.0833},
        {"name": "Яйца", "item_type": "consumable", "price": 120, "qty": 10, "unit": "шт", "daily_use": 2, "base_price": 120, "period_years": 0.0833},
        {"name": "Макароны и мука", "item_type": "consumable", "price": 100, "qty": 2, "unit": "кг", "daily_use": 0.07, "base_price": 100, "period_years": 0.0833},
    ],
    "ss_home_chem": [
        {"name": "Стиральный порошок", "item_type": "consumable", "price": 350, "qty": 3, "unit": "кг", "daily_use": 0.05, "base_price": 350, "period_years": 0.1667},
        {"name": "Средство для посуды", "item_type": "consumable", "price": 150, "qty": 500, "unit": "мл", "daily_use": 10, "base_price": 150, "period_years": 0.0833},
        {"name": "Чистящие средства", "item_type": "consumable", "price": 200, "qty": 1, "unit": "шт", "daily_use": 0.03, "base_price": 200, "period_years": 0.0833},
        {"name": "Губки и тряпки", "item_type": "consumable", "price": 100, "qty": 5, "unit": "шт", "daily_use": 0.1, "base_price": 100, "period_years": 0.0833},
        {"name": "Мусорные пакеты", "item_type": "consumable", "price": 80, "qty": 30, "unit": "шт", "daily_use": 1, "base_price": 80, "period_years": 0.0833},
        {"name": "Кондиционер для белья", "item_type": "consumable", "price": 250, "qty": 1, "unit": "л", "daily_use": 0.02, "base_price": 250, "period_years": 0.1667},
    ],
    "ss_cloth_base": [
        {"name": "Футболки (5 шт)", "item_type": "wear", "price": 5000, "base_price": 5000, "period_years": 1, "wear_life_weeks": 52},
        {"name": "Джинсы (2 шт)", "item_type": "wear", "price": 6000, "base_price": 6000, "period_years": 1.5, "wear_life_weeks": 78},
        {"name": "Кроссовки", "item_type": "wear", "price": 8000, "base_price": 8000, "period_years": 1, "wear_life_weeks": 52},
        {"name": "Куртка", "item_type": "wear", "price": 12000, "base_price": 12000, "period_years": 3, "wear_life_weeks": 156},
        {"name": "Носки (10 пар)", "item_type": "wear", "price": 1500, "base_price": 1500, "period_years": 0.5, "wear_life_weeks": 26},
        {"name": "Нижнее белье (5 шт)", "item_type": "wear", "price": 2500, "base_price": 2500, "period_years": 1, "wear_life_weeks": 52},
        {"name": "Свитер/худи", "item_type": "wear", "price": 4000, "base_price": 4000, "period_years": 2, "wear_life_weeks": 104},
        {"name": "Шорты/юбка", "item_type": "wear", "price": 2000, "base_price": 2000, "period_years": 2, "wear_life_weeks": 104},
        {"name": "Домашняя одежда", "item_type": "wear", "price": 1000, "base_price": 1000, "period_years": 1, "wear_life_weeks": 52},
    ],
    "ss_food_snack": [
        {"name": "Шоколад и конфеты", "item_type": "consumable", "price": 300, "qty": 500, "unit": "г", "daily_use": 30, "base_price": 300, "period_years": 0.0833},
        {"name": "Кофе и чай", "item_type": "consumable", "price": 600, "qty": 500, "unit": "г", "daily_use": 15, "base_price": 600, "period_years": 0.0833},
        {"name": "Соки и напитки", "item_type": "consumable", "price": 200, "qty": 2, "unit": "л", "daily_use": 0.2, "base_price": 200, "period_years": 0.0833},
        {"name": "Печенье и снеки", "item_type": "consumable", "price": 250, "qty": 500, "unit": "г", "daily_use": 30, "base_price": 250, "period_years": 0.0833},
    ],
    "ss_auto_pub": [
        {"name": "Проездной ЕТК", "item_type": "consumable", "price": 2500, "qty": 1, "unit": "шт", "daily_use": 0.033, "base_price": 2500, "period_years": 0.0833},
        {"name": "Такси (резерв)", "item_type": "consumable", "price": 700, "qty": 1, "unit": "шт", "daily_use": 0.033, "base_price": 700, "period_years": 0.0833},
    ],
    "ss_care_base": [
        {"name": "Шампунь", "item_type": "consumable", "price": 350, "qty": 400, "unit": "мл", "daily_use": 10, "base_price": 350, "period_years": 0.0833},
        {"name": "Гель для душа", "item_type": "consumable", "price": 250, "qty": 500, "unit": "мл", "daily_use": 15, "base_price": 250, "period_years": 0.0833},
        {"name": "Крем", "item_type": "consumable", "price": 400, "qty": 50, "unit": "мл", "daily_use": 1, "base_price": 400, "period_years": 0.0833},
        {"name": "Зубная паста", "item_type": "consumable", "price": 200, "qty": 100, "unit": "мл", "daily_use": 2, "base_price": 200, "period_years": 0.0833},
        {"name": "Дезодорант", "item_type": "consumable", "price": 300, "qty": 150, "unit": "мл", "daily_use": 3, "base_price": 300, "period_years": 0.0833},
        {"name": "Зубная щетка", "item_type": "wear", "price": 200, "base_price": 200, "period_years": 0.25, "wear_life_weeks": 13},
        {"name": "Бритва", "item_type": "consumable", "price": 500, "qty": 4, "unit": "шт", "daily_use": 0.14, "base_price": 500, "period_years": 0.0833},
    ],
    "ss_fun_gifts": [
        {"name": "Подарки на ДР", "item_type": "consumable", "price": 15000, "qty": 1, "unit": "шт", "daily_use": 0.0027, "base_price": 15000, "period_years": 1},
        {"name": "Новый год", "item_type": "consumable", "price": 5000, "qty": 1, "unit": "шт", "daily_use": 0.0027, "base_price": 5000, "period_years": 1},
        {"name": "8 марта / 23 февраля", "item_type": "consumable", "price": 3000, "qty": 1, "unit": "шт", "daily_use": 0.0027, "base_price": 3000, "period_years": 1},
    ],
    "ss_care_skin": [
        {"name": "Очищающая пенка", "item_type": "consumable", "price": 800, "qty": 150, "unit": "мл", "daily_use": 3, "base_price": 800, "period_years": 0.0833},
        {"name": "Тонер", "item_type": "consumable", "price": 1200, "qty": 200, "unit": "мл", "daily_use": 3, "base_price": 1200, "period_years": 0.0833},
        {"name": "Крем для лица", "item_type": "consumable", "price": 1500, "qty": 50, "unit": "мл", "daily_use": 1, "base_price": 1500, "period_years": 0.0833},
        {"name": "SPF крем", "item_type": "consumable", "price": 900, "qty": 50, "unit": "мл", "daily_use": 1.5, "base_price": 900, "period_years": 0.0833},
    ],
    "ss_cloth_sport": [
        {"name": "Спортивные штаны", "item_type": "wear", "price": 3000, "base_price": 3000, "period_years": 1.5, "wear_life_weeks": 78},
        {"name": "Спортивная футболка (3 шт)", "item_type": "wear", "price": 3000, "base_price": 3000, "period_years": 1, "wear_life_weeks": 52},
        {"name": "Кроссовки для зала", "item_type": "wear", "price": 6000, "base_price": 6000, "period_years": 1.5, "wear_life_weeks": 78},
        {"name": "Спортивные носки (5 пар)", "item_type": "wear", "price": 1000, "base_price": 1000, "period_years": 0.5, "wear_life_weeks": 26},
        {"name": "Шорты спортивные", "item_type": "wear", "price": 2000, "base_price": 2000, "period_years": 2, "wear_life_weeks": 104},
        {"name": "Ветровка", "item_type": "wear", "price": 3000, "base_price": 3000, "period_years": 3, "wear_life_weeks": 156},
    ],
}


def upgrade() -> None:
    """Insert SmartSpend demo sets with items."""
    sets_table = sa.table(
        "sets",
        sa.column("id", sa.String),
        sa.column("source", sa.String),
        sa.column("category_id", sa.String),
        sa.column("set_type", sa.String),
        sa.column("color", sa.String),
        sa.column("title", sa.String),
        sa.column("description", sa.Text),
        sa.column("amount", sa.Integer),
        sa.column("amount_label", sa.String),
        sa.column("users_count", sa.Integer),
        sa.column("is_private", sa.Boolean),
        sa.column("hidden", sa.Boolean),
        sa.column("about_title", sa.String),
        sa.column("about_text", sa.Text),
    )
    op.bulk_insert(sets_table, SETS)

    items_table = sa.table(
        "set_items",
        sa.column("set_id", sa.String),
        sa.column("name", sa.String),
        sa.column("item_type", sa.String),
        sa.column("price", sa.Integer),
        sa.column("qty", sa.Numeric),
        sa.column("unit", sa.String),
        sa.column("daily_use", sa.Numeric),
        sa.column("wear_life_weeks", sa.Integer),
        sa.column("purchase_date", sa.Date),
        sa.column("planned_price", sa.Integer),
        sa.column("base_price", sa.Numeric),
        sa.column("period_years", sa.Numeric),
    )
    rows = []
    for set_id, items in ITEMS.items():
        for item in items:
            rows.append({
                "set_id": set_id,
                "name": item["name"],
                "item_type": item.get("item_type", "consumable"),
                "price": item.get("price", 0),
                "qty": item.get("qty"),
                "unit": item.get("unit"),
                "daily_use": item.get("daily_use"),
                "wear_life_weeks": item.get("wear_life_weeks"),
                "purchase_date": None,
                "planned_price": None,
                "base_price": item.get("base_price"),
                "period_years": item.get("period_years"),
            })
    op.bulk_insert(items_table, rows)


def downgrade() -> None:
    """Remove SmartSpend demo sets."""
    set_ids = [s["id"] for s in SETS]
    ids_str = ", ".join(f"'{sid}'" for sid in set_ids)
    op.execute(f"DELETE FROM set_items WHERE set_id IN ({ids_str})")
    op.execute(f"DELETE FROM sets WHERE id IN ({ids_str})")
