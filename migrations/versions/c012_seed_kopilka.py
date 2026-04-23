"""seed deposits, companies, promos

Revision ID: c012_seed_kopilka
Revises: c011_promo_fields
Create Date: 2026-04-23 14:00:00.000000
"""

from typing import Sequence, Union

import json

import sqlalchemy as sa
from alembic import op

revision: str = "c012_seed_kopilka"
down_revision: Union[str, None] = "c011_promo_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── DEPOSITS ──
    deposits = [
        dict(id="d1", bank_name="Т-Банк", bank_color="#FFDD2D", bank_text_color="#1A1A1A", name="СмartВклад Онлайн", rates={"1": 14.0, "2": 16.5, "3": 21.5, "6": 20.0, "12": 18.5, "18": 17.0}, min_amount=50000, max_amount=None, replenishment=False, withdrawal=False, freq="end", is_systemic=True, conditions=["new_client"], tags=["для новых клиентов", "выплата % в конце срока", "без пополнения и снятия"], conditions_text="Только для новых клиентов банка. Открытие онлайн через приложение.", params="Выплата процентов в конце срока. Капитализация: нет."),
        dict(id="d2", bank_name="Альфа-Банк", bank_color="#EF3124", bank_text_color="#FFF", name="Альфа-Вклад", rates={"1": 13.5, "3": 20.8, "6": 19.5, "12": 18.0, "18": 16.5, "24": 15.5}, min_amount=10000, max_amount=None, replenishment=True, withdrawal=False, freq="monthly", is_systemic=True, conditions=["no_extra"], tags=["выплата % ежемесячно", "с пополнением"], conditions_text="Для новых и действующих клиентов. Пополнение разрешено.", params="Выплата процентов ежемесячно. Пополнение: да. Снятие: нет."),
        dict(id="d3", bank_name="Сбер", bank_color="#21A038", bank_text_color="#FFF", name="Лучший %", rates={"1": 12.0, "2": 15.5, "3": 19.0, "4": 18.0, "5": 17.5, "6": 18.5, "12": 17.0, "18": 15.5, "24": 14.0, "36": 13.0}, min_amount=1000, max_amount=None, replenishment=True, withdrawal=False, freq="monthly", is_systemic=True, conditions=["no_extra"], tags=["с пополнением", "выплата % ежемесячно"], conditions_text="Для всех клиентов. От 1 000 руб.", params="Выплата процентов ежемесячно. Капитализация: доступна."),
        dict(id="d4", bank_name="ВТБ", bank_color="#009FDF", bank_text_color="#FFF", name="Новое время", rates={"3": 20.0, "4": 19.0, "5": 18.5, "6": 19.5, "12": 18.0, "18": 16.0}, min_amount=30000, max_amount=None, replenishment=False, withdrawal=False, freq="end", is_systemic=True, conditions=["new_client", "new_money"], tags=["для новых клиентов", "выплата % в конце срока", "без пополнения и снятия"], conditions_text="Только для новых клиентов. Только новые деньги.", params="Выплата в конце срока. Без пополнения и снятия."),
        dict(id="d5", bank_name="Газпромбанк", bank_color="#003087", bank_text_color="#FFF", name="Накопи +", rates={"3": 19.5, "6": 19.0, "12": 17.5, "18": 16.0, "24": 15.0, "36": 13.5}, min_amount=15000, max_amount=None, replenishment=True, withdrawal=False, freq="end", is_systemic=True, conditions=["no_extra"], tags=["с пополнением", "выплата % в конце срока"], conditions_text="Открытие в офисе или через ЛК. Пополнение разрешено.", params="Выплата в конце срока. Снятие: нет."),
        dict(id="d6", bank_name="Банк Дом.РФ", bank_color="#1A3F6F", bank_text_color="#FFF", name="Надёжный прайм", rates={"1": 13.0, "2": 17.0, "3": 20.5, "6": 18.0}, min_amount=100000, max_amount=30000000, replenishment=False, withdrawal=False, freq="end", is_systemic=True, conditions=["new_client"], tags=["для новых клиентов", "выплата % в конце срока", "без пополнения и снятия"], conditions_text="Для новых клиентов. От 100 000 руб.", params="Без пополнения и снятия. Выплата в конце срока."),
        dict(id="d7", bank_name="МТС Банк", bank_color="#E30611", bank_text_color="#FFF", name="МТС Специальный", rates={"3": 20.2, "6": 19.0, "12": 17.0}, min_amount=10000, max_amount=5000000, replenishment=False, withdrawal=False, freq="end", is_systemic=False, conditions=["insurance"], tags=["инвест или страхование", "выплата % в конце срока", "без пополнения и снятия"], conditions_text="Требуется оформление инвестиционных или страховых продуктов.", params="Без пополнения и снятия. Выплата в конце срока."),
        dict(id="d8", bank_name="Росбанк", bank_color="#CC2030", bank_text_color="#FFF", name="Максимальный доход", rates={"1": 12.5, "2": 16.0, "3": 19.8, "6": 18.5, "12": 17.0, "18": 15.5}, min_amount=50000, max_amount=None, replenishment=False, withdrawal=False, freq="end", is_systemic=True, conditions=["no_extra"], tags=["выплата % в конце срока", "без пополнения и снятия"], conditions_text="Для новых и действующих клиентов.", params="Выплата в конце срока. Без пополнения и снятия."),
        dict(id="d9", bank_name="Сбер", bank_color="#21A038", bank_text_color="#FFF", name="Пенсионный плюс", rates={"3": 20.5, "6": 20.0, "12": 18.5, "18": 17.0}, min_amount=1000, max_amount=None, replenishment=True, withdrawal=False, freq="monthly", is_systemic=True, conditions=["pension"], tags=["для пенсионеров", "с пополнением", "выплата % ежемесячно"], conditions_text="Только для получателей пенсии на счёт в Сбере.", params="Выплата процентов ежемесячно. Пополнение: да."),
        dict(id="d10", bank_name="Т-Банк", bank_color="#FFDD2D", bank_text_color="#1A1A1A", name="Т-Привилегия", rates={"1": 16.0, "3": 22.5, "6": 21.0, "12": 19.5}, min_amount=300000, max_amount=None, replenishment=False, withdrawal=False, freq="end", is_systemic=True, conditions=["premium"], tags=["премиальный клиент", "выплата % в конце срока"], conditions_text="Только для клиентов с пакетом Т-Привилегия или Т-Прайм.", params="Выплата в конце срока. Без пополнения и снятия."),
    ]

    for d in deposits:
        conn.execute(sa.text(
            "INSERT INTO deposits (id, bank_name, bank_color, bank_text_color, name, rates, min_amount, max_amount, replenishment, withdrawal, freq, is_systemic, conditions, tags, conditions_text, params) "
            "VALUES (:id, :bank_name, :bank_color, :bank_text_color, :name, CAST(:rates AS jsonb), :min_amount, :max_amount, :replenishment, :withdrawal, :freq, :is_systemic, :conditions, :tags, :conditions_text, :params) "
            "ON CONFLICT (id) DO NOTHING"
        ), {
            **d,
            "rates": json.dumps(d["rates"]),
            "conditions": d["conditions"],
            "tags": d["tags"],
        })

    # ── COMPANIES ──
    companies = [
        ("c-perekrestok", "Перекрёсток", "Пе", "#4E8268", "food", "Сеть супермаркетов с широким ассортиментом продуктов.", ["events", "broadcast"]),
        ("c-magnit", "Магнит", "Ма", "#DA4040", "food", "Крупнейшая розничная сеть России.", ["coupons", "events"]),
        ("c-vkusvill", "ВкусВилл", "Вк", "#6DB880", "food", "Натуральные продукты без лишних добавок.", ["coupons", "broadcast"]),
        ("c-lenta", "Лента", "Ле", "#C8A840", "food", "Гипермаркеты и супермаркеты по всей России.", ["events", "broadcast"]),
        ("c-samokat", "Самокат", "Са", "#F04060", "food", "Доставка продуктов за 15 минут.", ["coupons", "events"]),
        ("c-pyaterochka", "Пятёрочка", "Пя", "#C83030", "food", "Магазины у дома от X5 Group.", ["events", "coupons"]),
        ("c-vkusno", "Вкусно и точка", "Вт", "#DA4040", "cafe", "Российская сеть фастфуда.", ["events", "coupons"]),
        ("c-kfc", "KFC", "KF", "#C8362A", "cafe", "Международная сеть ресторанов быстрого питания.", ["events", "coupons"]),
        ("c-dodo", "Додо Пицца", "До", "#F04040", "cafe", "Крупнейшая пиццерия России.", ["events", "broadcast"]),
        ("c-yandex-go", "Яндекс Go", "Яг", "#E8C820", "transport", "Приложение для такси и каршеринга.", ["coupons", "events"]),
        ("c-rosneft", "Роснефть", "Рн", "#DA4040", "transport", "Крупнейшая нефтяная компания России.", ["events", "broadcast"]),
        ("c-mvideo", "М.Видео", "МВ", "#DA4040", "home", "Крупнейшая сеть магазинов электроники.", ["events", "broadcast"]),
        ("c-eldorado", "Эльдорадо", "Эл", "#2A80C8", "home", "Магазины электроники и техники.", ["events", "coupons"]),
        ("c-lerua", "Леруа Мерлен", "Лм", "#4E8830", "home", "Гипермаркеты для ремонта и строительства.", ["events", "broadcast"]),
        ("c-wb", "Wildberries", "WB", "#8A40C8", "clothes", "Крупнейший маркетплейс России.", ["events", "coupons", "broadcast"]),
        ("c-ozon", "Ozon", "Oz", "#4A5FAE", "clothes", "Универсальный маркетплейс.", ["events", "coupons", "broadcast"]),
        ("c-lamoda", "Lamoda", "La", "#333333", "clothes", "Онлайн-магазин fashion-брендов.", ["coupons", "events"]),
        ("c-yandex-plus", "Яндекс Плюс", "Яп", "#E8C820", "leisure", "Подписка с кешбэком во всех сервисах Яндекса.", ["coupons", "events", "broadcast"]),
        ("c-apteka", "Аптека.ру", "Ап", "#4E8268", "health", "Онлайн-аптека с доставкой.", ["coupons", "events"]),
        ("c-rigla", "Ригла", "Ри", "#22A870", "health", "Аптечная сеть с картой лояльности.", ["events", "broadcast"]),
        ("c-letual", "Л'Этуаль", "Лэ", "#C83080", "health", "Парфюмерия и косметика.", ["coupons", "events"]),
        ("c-skyeng", "Skyeng", "Sk", "#4A5FAE", "education", "Онлайн-школа английского языка.", ["coupons", "events"]),
        ("c-skillbox", "Skillbox", "Sb", "#5848C8", "education", "Онлайн-университет для цифровых профессий.", ["coupons", "events"]),
        ("c-detmir", "Детский Мир", "Дм", "#C82828", "education", "Магазины для детей.", ["events", "broadcast", "coupons"]),
        ("c-rzd", "РЖД", "РЖ", "#DA2828", "travel", "Железнодорожный перевозчик.", ["events", "broadcast"]),
        ("c-aeroflot", "Аэрофлот", "Аэ", "#2848A8", "travel", "Национальный авиаперевозчик.", ["events", "broadcast"]),
        ("c-aviasales", "Авиасейлс", "Ав", "#FF6040", "travel", "Поиск дешёвых авиабилетов.", ["events", "coupons"]),
        ("c-sber", "СберБанк", "Сб", "#22C870", "other", "Крупнейший банк России.", ["events", "broadcast"]),
        ("c-tinkoff", "Т-Банк", "ТБ", "#E8C820", "other", "Цифровой банк без офисов.", ["coupons", "events", "broadcast"]),
        ("c-vtb", "ВТБ", "ВТ", "#2440A8", "other", "Государственный банк.", ["events", "broadcast"]),
        ("c-mts", "МТС", "МТ", "#DA2020", "other", "Мобильный оператор.", ["events", "coupons", "broadcast"]),
    ]

    for c in companies:
        conn.execute(sa.text(
            "INSERT INTO companies (id, name, abbr, color, category_id, description, promo_types) "
            "VALUES (:id, :name, :abbr, :color, :cat, :desc, :pt) "
            "ON CONFLICT (id) DO NOTHING"
        ), {"id": c[0], "name": c[1], "abbr": c[2], "color": c[3], "cat": c[4], "desc": c[5], "pt": c[6]})

    # ── PROMOS (sample) ──
    promos = [
        ("broadcast", "c-perekrestok", "food", None, "Скидка 20% на все фрукты и овощи каждую пятницу и субботу! Заходите.", None, "Telegram", "https://t.me/perekrestok", None, None),
        ("broadcast", "c-vkusvill", "food", None, "Новинка: боул с киноа и запечёнными овощами — всего 299 руб.", None, "Telegram", "https://t.me/vkusvill", None, None),
        ("broadcast", "c-wb", "clothes", None, "Стартовала Неделя брендов — скидки до 50% на топовые марки одежды и обуви.", None, "Telegram", "https://t.me/wildberries_official", None, None),
        ("broadcast", "c-dodo", "cafe", None, "Акция 2 по цене 1 продлена до конца марта! Бесплатная доставка от 600 руб.", None, "Telegram", "https://t.me/dodopizza", None, None),
        ("event", "c-perekrestok", "food", "Скидка 20% на фрукты и овощи", "Каждую пятницу и субботу — скидка 20% на весь отдел свежих фруктов и овощей.", None, None, None, None, "regular"),
        ("coupon", "c-vkusvill", "food", "Скидка 500 руб на первый заказ", "Промокод действует на первый заказ от 1 500 руб через приложение ВкусВилл.", "SMART500", None, "https://vkusvill.ru/promo/", None, "new_clients"),
        ("event", "c-wb", "clothes", "Недели брендов: скидки до 50%", "Акция на топ-бренды одежды и обуви. Скидки до 50% без промокодов.", None, None, None, None, "holiday"),
        ("coupon", "c-dodo", "cafe", "2 пиццы по цене 1", "При заказе от двух пицц одного размера — вторая в подарок.", "DODO2X1", None, "https://dodopizza.ru/promo/", None, "regular"),
        ("event", "c-mvideo", "home", "Гарантия лучшей цены на технику", "М.Видео вернёт разницу, если найдёте дешевле.", None, None, None, None, "regular"),
        ("coupon", "c-yandex-plus", "leisure", "3 месяца Яндекс Плюс бесплатно", "Подключите Яндекс Плюс по промокоду и получите 3 месяца бесплатно.", "PLUS3FREE", None, "https://plus.yandex.ru/promo/", None, "new_clients"),
        ("event", "c-rigla", "health", "Скидка 15% на витамины", "Весенняя акция на витамины и БАДы в аптеках сети Ригла.", None, None, None, None, "regular"),
        ("coupon", "c-letual", "health", "Скидка 20% в день рождения", "В течение двух недель до и после дня рождения — скидка 20%.", "BD20LET", None, "https://letu.ru/loyalty/birthday/", None, "birthday"),
        ("coupon", "c-skyeng", "education", "Скидка 20% на первый месяц", "Промокод для новых учеников Skyeng.", "SKY20NEW", None, "https://skyeng.ru/promo/", None, "new_clients"),
        ("event", "c-rzd", "travel", "Акция Весенние путешествия", "Скидки до 30% на билеты при покупке за 45+ дней до отправления.", None, None, None, None, "holiday"),
        ("whisper", "c-magnit", "food", "Скидка 15% при оплате через СБП в приложении Магнит", "Работает только в приложении, не в браузере. Раздел Акции — Оплата СБП.", None, None, None, None, None),
        ("whisper", "c-wb", "clothes", "500 руб скидка на первый заказ по промокоду", "Только для новых аккаунтов. Вводить при оформлении.", "WB500NEW", None, "https://wildberries.ru/promo/", None, "new_clients"),
        ("whisper", "c-ozon", "clothes", "Кешбэк 10% баллами на первый заказ", "Баллы начисляются в течение 3 дней. Можно потратить на следующий заказ.", None, None, None, None, "new_clients"),
        ("whisper", "c-sber", "other", "Повышенный кешбэк 5% на АЗС через СберСпасибо", "Нужно активировать категорию в приложении. Работает на всех АЗС.", None, None, None, None, None),
    ]

    for p in promos:
        conn.execute(sa.text(
            "INSERT INTO promos (type, company_id, category_id, title, text, code, channel, url, source_url, promo_filter) "
            "VALUES (:type, :company_id, :category_id, :title, :text, :code, :channel, :url, :source_url, :promo_filter)"
        ), {
            "type": p[0], "company_id": p[1], "category_id": p[2], "title": p[3],
            "text": p[4], "code": p[5], "channel": p[6], "url": p[7],
            "source_url": p[8], "promo_filter": p[9],
        })

    # ── CARDS ──
    cards = [
        dict(id="c1", bank_name="Т-Банк", bank_color="#FFDD2D", bank_text_color="#1A1A1A", name="Блэк", card_type="debit", cashback={"food":1,"cafe":1,"transport":1,"home":1,"clothes":1,"health":1,"leisure":1,"travel":1,"other":1}, cashback_note="до 5% на выбранные категории, до 15% у партнёров", grace_days=0, fee=0, fee_base=99, is_systemic=True, conditions=["no_extra"], tags=["1% на всё","до 15% у партнёров","бесплатное обслуживание"], bonus_type="rubles", bonus_system="Кешбэк рублями", bonus_desc="1% на все покупки. До 5% на выбранные категории. До 15% у партнёров.", fee_desc="Бесплатно при тратах от 30 000 руб/мес. Иначе 99 руб/мес.", url="https://www.tbank.ru/tbank-black/"),
        dict(id="c2", bank_name="Т-Банк", bank_color="#FFDD2D", bank_text_color="#1A1A1A", name="Платинум", card_type="credit", cashback={"other":1}, cashback_note="до 30% у партнёров", grace_days=55, fee=590, fee_base=590, is_systemic=True, conditions=["no_extra"], tags=["55 дней без %","1% кешбэк"], bonus_type="rubles", bonus_system="Льготный период + кешбэк", bonus_desc="55 дней без процентов. 1% кешбэк. До 30% у партнёров.", fee_desc="590 руб/год.", url="https://www.tbank.ru/credit-card/tinkoff-platinum/"),
        dict(id="c3", bank_name="Альфа-Банк", bank_color="#EF3124", bank_text_color="#FFF", name="Кэшбэк", card_type="debit", cashback={"food":5,"cafe":5,"transport":5,"other":1}, cashback_note="до 5% на 3 категории на выбор", grace_days=0, fee=0, fee_base=149, is_systemic=True, conditions=["no_extra"], tags=["до 5% на категории","1% на остальное"], bonus_type="rubles", bonus_system="Кешбэк рублями", bonus_desc="До 5% на 3 категории на выбор. 1% на всё остальное.", fee_desc="Бесплатно при тратах от 10 000 руб/мес. Иначе 149 руб/мес.", url="https://www.alfabank.ru/get-money/cashback/"),
        dict(id="c4", bank_name="Альфа-Банк", bank_color="#EF3124", bank_text_color="#FFF", name="100 дней", card_type="credit", cashback={"other":1}, cashback_note="1% на всё", grace_days=100, fee=0, fee_base=1490, is_systemic=True, conditions=["no_extra"], tags=["100 дней без %"], bonus_type="rubles", bonus_system="Льготный период + кешбэк", bonus_desc="100 дней без процентов. 1% кешбэк.", fee_desc="Первый год бесплатно. Далее 1 490 руб/год.", url="https://www.alfabank.ru/get-money/credit-cards/100-days/"),
        dict(id="c5", bank_name="Сбер", bank_color="#21A038", bank_text_color="#FFF", name="СберКарта", card_type="debit", cashback={"food":0.5,"cafe":0.5,"transport":0.5,"home":0.5,"clothes":0.5,"health":0.5,"leisure":0.5,"travel":0.5,"other":0.5}, cashback_note="до 30% у партнёров СберСпасибо", grace_days=0, fee=0, fee_base=0, is_systemic=True, conditions=["no_extra"], tags=["0.5% Спасибо","до 30% у партнёров"], bonus_type="points", bonus_system="Бонусы СберСпасибо", bonus_desc="0.5% бонусами Спасибо на все покупки. До 30% у партнёров.", fee_desc="Обслуживание бесплатно.", url="https://www.sberbank.ru/ru/person/bank_cards/debet/sbercard/"),
        dict(id="c6", bank_name="ВТБ", bank_color="#009FDF", bank_text_color="#FFF", name="Мультикарта", card_type="debit", cashback={"food":1.5,"cafe":1.5,"transport":1.5,"home":1.5,"clothes":1.5,"health":1.5,"leisure":1.5,"travel":1.5,"other":1.5}, cashback_note="до 2% при тратах от 75 000 руб/мес", grace_days=0, fee=0, fee_base=249, is_systemic=True, conditions=["salary","no_extra"], tags=["1.5% на всё","зарплатный проект"], bonus_type="rubles", bonus_system="Кешбэк рублями", bonus_desc="1.5% на все покупки. 2% при тратах от 75 000 руб/мес.", fee_desc="Бесплатно при тратах от 5 000 руб/мес. Иначе 249 руб/мес.", url="https://www.vtb.ru/personal/karty/multicard/"),
        dict(id="c7", bank_name="Газпромбанк", bank_color="#003087", bank_text_color="#FFF", name="МИР Supreme", card_type="debit", cashback={"food":2,"transport":3,"other":1}, cashback_note="3% АЗС, 2% продукты, 1% остальное", grace_days=0, fee=0, fee_base=0, is_systemic=True, conditions=["no_extra"], tags=["3% на АЗС","2% продукты","бесплатно"], bonus_type="rubles", bonus_system="Кешбэк рублями", bonus_desc="3% на АЗС. 2% на продукты. 1% на остальное.", fee_desc="Обслуживание бесплатно.", url="https://www.gazprombank.ru/personal/bank-cards/debit-cards/mir-supreme/"),
        dict(id="c8", bank_name="МТС Банк", bank_color="#E30611", bank_text_color="#FFF", name="Cash Back", card_type="debit", cashback={"cafe":5,"transport":5,"other":1}, cashback_note="5% кафе и транспорт", grace_days=0, fee=0, fee_base=99, is_systemic=False, conditions=["no_extra"], tags=["5% кафе и транспорт","1% на остальное"], bonus_type="rubles", bonus_system="Кешбэк рублями", bonus_desc="5% на кафе и транспорт. 1% на остальное.", fee_desc="Бесплатно при тратах от 15 000 руб/мес. Иначе 99 руб/мес.", url="https://www.mtsbank.ru/karta-cash-back/"),
        dict(id="c9", bank_name="Росбанк", bank_color="#CC2030", bank_text_color="#FFF", name="#МожноВСЁ", card_type="debit", cashback={"food":3,"cafe":3,"transport":3,"home":3,"clothes":3,"health":3,"leisure":3,"travel":3,"other":1}, cashback_note="3% на 3 категории на выбор", grace_days=0, fee=0, fee_base=99, is_systemic=True, conditions=["no_extra"], tags=["3% на категории","1% остальное"], bonus_type="rubles", bonus_system="Кешбэк рублями", bonus_desc="3% на 3 категории на выбор. 1% на остальное.", fee_desc="Бесплатно при тратах от 15 000 руб/мес. Иначе 99 руб/мес.", url="https://www.rosbank.ru/card/mozhno-vsyo/"),
        dict(id="c10", bank_name="Банк Дом.РФ", bank_color="#1A3F6F", bank_text_color="#FFF", name="Умная карта", card_type="debit", cashback={"food":2,"cafe":2,"transport":2,"home":2,"clothes":2,"health":2,"leisure":2,"travel":2,"other":2}, cashback_note="5% на крупнейшую категорию автоматически", grace_days=0, fee=0, fee_base=99, is_systemic=True, conditions=["no_extra"], tags=["2% на всё","5% топ-категория"], bonus_type="rubles", bonus_system="Умный кешбэк", bonus_desc="2% на все покупки. 5% на категорию с наибольшими тратами.", fee_desc="Бесплатно при тратах от 10 000 руб/мес. Иначе 99 руб/мес.", url="https://domrfbank.ru/cards/umkarta/"),
        dict(id="c11", bank_name="Совкомбанк", bank_color="#6B3FA0", bank_text_color="#FFF", name="Халва", card_type="credit", cashback={"food":1.5,"cafe":1.5,"transport":1.5,"home":1.5,"clothes":1.5,"health":1.5,"leisure":1.5,"travel":1.5,"other":1.5}, cashback_note="рассрочка до 36 мес у партнёров", grace_days=0, fee=0, fee_base=0, is_systemic=True, conditions=["no_extra"], tags=["рассрочка 0%","1.5% кешбэк","бесплатно"], bonus_type="rubles", bonus_system="Рассрочка + кешбэк", bonus_desc="Рассрочка до 36 месяцев у партнёров. 1.5% кешбэк.", fee_desc="Обслуживание бесплатно.", url="https://sovcombank.ru/cards/halva/"),
        dict(id="c12", bank_name="Сбер", bank_color="#21A038", bank_text_color="#FFF", name="СберПрайм+", card_type="debit", cashback={"food":5,"cafe":5,"transport":3,"home":3,"clothes":3,"health":3,"leisure":3,"travel":5,"other":1.5}, cashback_note="до 10% у партнёров, подписка СберПрайм", grace_days=0, fee=0, fee_base=0, is_systemic=True, conditions=["premium","subscription"], tags=["до 10% Спасибо","подписка СберПрайм","премиальная"], bonus_type="points", bonus_system="Повышенный СберСпасибо", bonus_desc="До 10% бонусами Спасибо. 5% на продукты, кафе и путешествия.", fee_desc="Бесплатно при подписке СберПрайм (от 399 руб/мес).", url="https://www.sberbank.ru/ru/person/subscriptions/sberprime/"),
    ]

    for card in cards:
        conn.execute(sa.text(
            "INSERT INTO cards (id, bank_name, bank_color, bank_text_color, name, card_type, cashback, cashback_note, "
            "grace_days, fee, fee_base, is_systemic, conditions, tags, bonus_type, bonus_system, bonus_desc, fee_desc, url) "
            "VALUES (:id, :bank_name, :bank_color, :bank_text_color, :name, :card_type, CAST(:cashback AS jsonb), :cashback_note, "
            ":grace_days, :fee, :fee_base, :is_systemic, :conditions, :tags, :bonus_type, :bonus_system, :bonus_desc, :fee_desc, :url) "
            "ON CONFLICT (id) DO NOTHING"
        ), {
            **card,
            "cashback": json.dumps(card["cashback"]) if card["cashback"] else None,
            "conditions": card["conditions"],
            "tags": card["tags"],
        })


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM cards"))
    conn.execute(sa.text("DELETE FROM promos"))
    conn.execute(sa.text("DELETE FROM companies"))
    conn.execute(sa.text("DELETE FROM deposits"))
