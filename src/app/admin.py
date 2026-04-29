from starlette.requests import Request
from starlette.responses import Response
from starlette_admin import action
from starlette_admin.auth import AdminUser, AuthProvider
from starlette_admin.contrib.sqla import Admin, ModelView

from src.app.core.config import settings
from src.app.core.database import engine
from src.app.models.article import Article
from src.app.models.card import Card
from src.app.models.company import Company
from src.app.models.deposit import Deposit
from src.app.models.notification import Notification
from src.app.models.promo import Promo
from src.app.models.set import Set
from src.app.models.user import User
from src.app.models.user_finance import UserFinance


class SmartSpendAuth(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request, response: Response
    ) -> Response:
        if username == "admin" and password == settings.admin_password:
            request.session.update({"username": username})
            return response
        raise Exception("Invalid credentials")

    async def is_authenticated(self, request: Request) -> bool:
        return request.session.get("username") == "admin"

    def get_admin_user(self, request: Request) -> AdminUser | None:
        username = request.session.get("username")
        if username:
            return AdminUser(username=username)
        return None

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response


class UserAdmin(ModelView):
    model = User
    name = "Пользователи"
    icon = "fa fa-users"
    fields = [
        User.id,
        User.email,
        User.display_name,
        User.username,
        User.initials,
        User.color,
        User.status,
        User.theme,
        User.bio,
        User.joined_at,
        User.deleted_at,
    ]
    column_list = [User.id, User.email, User.display_name, User.username, User.status, User.joined_at]
    column_searchable_list = [User.email, User.display_name, User.username]
    column_sortable_list = [User.email, User.display_name, User.joined_at, User.status]
    page_size = 25

    @action(name="suspend", text="Заблокировать", confirmation="Заблокировать выбранных?")
    async def suspend_action(self, request: Request, pks: list) -> str:
        session = request.state.session
        for pk in pks:
            user = await session.get(User, pk)
            if user:
                user.status = "suspended"
        await session.commit()
        return f"Заблокировано: {len(pks)}"

    @action(name="unsuspend", text="Разблокировать", confirmation="Разблокировать выбранных?")
    async def unsuspend_action(self, request: Request, pks: list) -> str:
        session = request.state.session
        for pk in pks:
            user = await session.get(User, pk)
            if user:
                user.status = "unverified"
        await session.commit()
        return f"Разблокировано: {len(pks)}"


class UserFinanceAdmin(ModelView):
    model = UserFinance
    name = "Финансы"
    icon = "fa fa-money"
    column_list = [UserFinance.user_id, UserFinance.income, UserFinance.housing, UserFinance.capital]
    page_size = 25


class SetAdmin(ModelView):
    model = Set
    name = "Наборы"
    icon = "fa fa-th-large"
    column_list = [Set.id, Set.title, Set.source, Set.category_id, Set.users_count, Set.is_private, Set.created_at]
    column_searchable_list = [Set.title, Set.description]
    column_sortable_list = [Set.title, Set.created_at, Set.users_count]
    page_size = 25


class ArticleAdmin(ModelView):
    model = Article
    name = "Статьи"
    icon = "fa fa-file-text"
    column_list = [
        Article.id,
        Article.title,
        Article.status,
        Article.is_private,
        Article.views_count,
        Article.created_at,
    ]
    column_searchable_list = [Article.title]
    column_sortable_list = [Article.title, Article.created_at, Article.views_count]
    page_size = 25


class DepositAdmin(ModelView):
    model = Deposit
    name = "Вклады"
    icon = "fa fa-bank"
    column_list = [Deposit.id, Deposit.bank_name, Deposit.name, Deposit.freq, Deposit.is_active]
    column_searchable_list = [Deposit.bank_name, Deposit.name]
    page_size = 25


class CardAdmin(ModelView):
    model = Card
    name = "Карты"
    icon = "fa fa-credit-card"
    column_list = [Card.id, Card.bank_name, Card.name, Card.card_type, Card.is_active]
    column_searchable_list = [Card.bank_name, Card.name]
    page_size = 25


class CompanyAdmin(ModelView):
    model = Company
    name = "Компании"
    icon = "fa fa-building"
    column_list = [Company.id, Company.name, Company.category_id, Company.is_active]
    column_searchable_list = [Company.name]
    page_size = 25


class PromoAdmin(ModelView):
    model = Promo
    name = "Промо"
    icon = "fa fa-tag"
    column_list = [
        Promo.id,
        Promo.type,
        Promo.title,
        Promo.company_id,
        Promo.votes_up,
        Promo.votes_down,
        Promo.is_active,
    ]
    column_searchable_list = [Promo.title, Promo.text]
    page_size = 25


class NotificationAdmin(ModelView):
    model = Notification
    name = "Уведомления"
    icon = "fa fa-bell"
    column_list = [Notification.id, Notification.user_id, Notification.type, Notification.title, Notification.is_read]
    page_size = 25


def setup_admin(app):
    admin = Admin(
        engine,
        title="SmartSpend Admin",
        auth_provider=SmartSpendAuth(login_path="/login", logout_path="/logout"),
    )
    admin.add_view(UserAdmin)
    admin.add_view(UserFinanceAdmin)
    admin.add_view(SetAdmin)
    admin.add_view(ArticleAdmin)
    admin.add_view(DepositAdmin)
    admin.add_view(CardAdmin)
    admin.add_view(CompanyAdmin)
    admin.add_view(PromoAdmin)
    admin.add_view(NotificationAdmin)
    admin.mount_to(app)
