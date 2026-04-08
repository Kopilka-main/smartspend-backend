"""seed articles from original frontend data

Revision ID: c004_seed_articles
Revises: c003_username
Create Date: 2026-04-05 14:00:00.000000
"""

from typing import Sequence, Union
from datetime import date

import sqlalchemy as sa
from alembic import op

revision: str = "c004_seed_articles"
down_revision: Union[str, None] = "c003_username"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ARTICLES = [
    {
        "id": "a1",
        "title": "Как перестать покупать ненужное: метод осознанного потребления",
        "article_type": "guide",
        "category_id": "other",
        "preview": "Каждый раз, когда вы открываете маркетплейс «просто посмотреть», алгоритмы уже знают, что вы купите. Разбираем механику импульсивных покупок и учимся её отключать.",
        "published_at": date(2026, 2, 15),
        "status": "published",
        "views_count": 1240,
        "likes_count": 342,
        "linked_set_id": "ss_food_base",
    },
    {
        "id": "a2",
        "title": "Инвентаризация жизни: почему важно знать, что у вас есть",
        "article_type": "guide",
        "category_id": "home",
        "preview": "Большинство людей не знают, что у них есть дома. Это приводит к дублированию покупок, просроченным продуктам и деньгам, выброшенным в мусор.",
        "published_at": date(2026, 1, 28),
        "status": "published",
        "views_count": 870,
        "likes_count": 218,
        "linked_set_id": "ss_food_base",
    },
    {
        "id": "a3",
        "title": "Smart-база: сколько на самом деле стоит ваш месяц",
        "article_type": "guide",
        "category_id": "other",
        "preview": "Smart-база — это точная стоимость одного месяца вашей жизни без излишеств. Узнайте, как её рассчитать и почему это главное число для финансовой безопасности.",
        "published_at": date(2026, 1, 10),
        "status": "published",
        "views_count": 2100,
        "likes_count": 487,
        "linked_set_id": "ss_food_base",
    },
]

BLOCKS = {
    "a1": [
        {"position": 0, "type": "p", "text": "Средний россиянин тратит на «незапланированные» покупки от 15 до 30% своего дохода. Это не слабость характера — это результат работы сотен инженеров и дизайнеров, задача которых — заставить вас потратить деньги прямо сейчас."},
        {"position": 1, "type": "h2", "title": "Как работает ловушка немедленного вознаграждения"},
        {"position": 2, "type": "p", "text": "Наш мозг плохо приспособлен к современным маркетплейсам. Эволюция научила нас хватать доступные ресурсы немедленно — потому что завтра их может не быть. Интернет-магазины эксплуатируют эту особенность: таймеры обратного отсчёта, «осталось 2 штуки», «только сегодня» — всё это искусственно созданный дефицит."},
        {"position": 3, "type": "highlight", "text": "Покупка ради покупки — это не потребление. Это способ управлять тревогой."},
        {"position": 4, "type": "h2", "title": "Метод 72 часов"},
        {"position": 5, "type": "p", "text": "Простое правило: если хочется купить что-то незапланированное — добавьте в отложенное и подождите 72 часа. Исследования показывают, что 80% таких желаний исчезают сами собой. Не потому что вещь плохая, а потому что желание было вызвано ситуацией, а не реальной потребностью."},
        {"position": 6, "type": "p", "text": "В SmartSpend мы реализуем этот принцип через систему наборов: вы заранее определяете, что вам нужно, и покупаете по списку, а не по настроению."},
        {"position": 7, "type": "h2", "title": "Три вопроса перед любой покупкой"},
        {"position": 8, "type": "ul", "items": ["Это решает реальную проблему, или мне просто нравится?", "Есть ли у меня уже что-то, что выполняет эту функцию?", "Буду ли я использовать это через 6 месяцев?"]},
        {"position": 9, "type": "p", "text": "Если хотя бы на один вопрос нет уверенного «да» — покупка, скорее всего, импульсивная. Сохраните деньги для чего-то, что действительно улучшит вашу жизнь."},
    ],
    "a2": [
        {"position": 0, "type": "p", "text": "Представьте: вы идёте в магазин и покупаете шампунь. Приходите домой и обнаруживаете, что у вас уже есть два запасных флакона. Знакомо? По статистике, около 25% продуктов питания в российских домохозяйствах выбрасывается, не будучи использованным."},
        {"position": 1, "type": "h2", "title": "Стоимость хаоса"},
        {"position": 2, "type": "p", "text": "Хаотичное управление запасами стоит денег. Дублирующиеся покупки, просроченные продукты, вещи купленные в панике по завышенной цене — всё это суммируется в тысячи рублей в год. Для семьи из трёх человек это может быть 40-60 тысяч рублей ежегодно."},
        {"position": 3, "type": "highlight", "text": "Инвентарь — это не про бережливость. Это про то, чтобы тратить деньги на то, что реально нужно."},
        {"position": 4, "type": "h2", "title": "Как начать инвентаризацию"},
        {"position": 5, "type": "ul", "items": ["Начните с одной категории: например, средства гигиены", "Запишите всё что есть и примерные остатки", "Добавьте в SmartSpend с указанием типа (расходное/ноское)", "Система сама рассчитает, когда нужно пополнить"]},
    ],
    "a3": [
        {"position": 0, "type": "p", "text": "Smart-база — это минимальная сумма, которая нужна вам в месяц для комфортной жизни без излишеств. Не нищенского существования, а нормальной жизни: еда, жильё, транспорт, базовые удовольствия. Это число — фундамент всей финансовой системы SmartSpend."},
        {"position": 1, "type": "h2", "title": "Почему это важно"},
        {"position": 2, "type": "p", "text": "Когда вы знаете свою Smart-базу, вы знаете цель для пассивного дохода. Safety Point — момент, когда ваши инвестиции генерируют пассивный доход, равный Smart-базе. После этого вы финансово защищены: даже если потеряете работу, система продолжает работать."},
        {"position": 3, "type": "highlight", "text": "Safety Point — это не пенсия. Это точка, с которой начинается настоящая свобода выбора."},
        {"position": 4, "type": "h2", "title": "Как рассчитать Smart-базу"},
        {"position": 5, "type": "ul", "items": ["Жильё (аренда или ипотека): ваша реальная сумма", "Продукты питания: для среднего россиянина ~12 000–18 000 ₽", "Транспорт (проездной или бензин): 3 000–8 000 ₽", "Коммунальные услуги: 4 000–8 000 ₽", "Средства гигиены и бытовая химия: 1 500–3 000 ₽", "Связь и интернет: 1 000–2 000 ₽", "Одежда и обувь (в пересчёте на месяц): 2 000–5 000 ₽"]},
        {"position": 6, "type": "p", "text": "Сложите всё — это и есть ваша Smart-база. Для одного человека в Москве без аренды это обычно 25 000–35 000 ₽. С арендой — 45 000–65 000 ₽."},
    ],
}


SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    users_table = sa.table(
        "users",
        sa.column("id", sa.dialects.postgresql.UUID),
        sa.column("email", sa.String),
        sa.column("password_hash", sa.String),
        sa.column("display_name", sa.String),
        sa.column("initials", sa.String),
        sa.column("color", sa.String),
        sa.column("status", sa.String),
        sa.column("theme", sa.String),
    )

    op.execute(
        users_table.insert().values(
            id=SYSTEM_USER_ID,
            email="system@smartspend.ru",
            password_hash="$2b$12$000000000000000000000000000000000000000000000000000000",
            display_name="Команда SmartSpend",
            initials="SS",
            color="#7DAF92",
            status="verified",
            theme="light",
        )
    )

    articles_table = sa.table(
        "articles",
        sa.column("id", sa.String),
        sa.column("title", sa.String),
        sa.column("article_type", sa.String),
        sa.column("category_id", sa.String),
        sa.column("preview", sa.Text),
        sa.column("published_at", sa.Date),
        sa.column("status", sa.String),
        sa.column("views_count", sa.Integer),
        sa.column("likes_count", sa.Integer),
        sa.column("dislikes_count", sa.Integer),
        sa.column("linked_set_id", sa.String),
        sa.column("author_id", sa.dialects.postgresql.UUID),
    )

    blocks_table = sa.table(
        "article_blocks",
        sa.column("article_id", sa.String),
        sa.column("position", sa.SmallInteger),
        sa.column("type", sa.String),
        sa.column("text", sa.Text),
        sa.column("html", sa.Text),
        sa.column("items", sa.ARRAY(sa.Text)),
        sa.column("title", sa.String),
    )

    for a in ARTICLES:
        op.execute(
            articles_table.insert().values(
                id=a["id"],
                title=a["title"],
                article_type=a["article_type"],
                category_id=a["category_id"],
                preview=a["preview"],
                published_at=a["published_at"],
                status=a["status"],
                views_count=a["views_count"],
                likes_count=a["likes_count"],
                dislikes_count=0,
                linked_set_id=a["linked_set_id"],
                author_id=SYSTEM_USER_ID,
            )
        )

    for article_id, blocks in BLOCKS.items():
        for b in blocks:
            op.execute(
                blocks_table.insert().values(
                    article_id=article_id,
                    position=b["position"],
                    type=b["type"],
                    text=b.get("text"),
                    html=None,
                    items=b.get("items"),
                    title=b.get("title"),
                )
            )


def downgrade() -> None:
    op.execute("DELETE FROM article_blocks WHERE article_id IN ('a1', 'a2', 'a3')")
    op.execute("DELETE FROM articles WHERE id IN ('a1', 'a2', 'a3')")
    op.execute(f"DELETE FROM users WHERE id = '{SYSTEM_USER_ID}'")
