from starlette.requests import Request
from starlette.responses import Response
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
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
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


def setup_admin(app):
    admin = Admin(
        engine,
        title="SmartSpend Admin",
        auth_provider=SmartSpendAuth(login_path="/login", logout_path="/logout"),
    )

    admin.add_view(
        ModelView(
            User,
            icon="fa fa-users",
            label="Пользователи",
            fields=[
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
            ],
            column_list=[User.id, User.email, User.display_name, User.username, User.status, User.joined_at],
            searchable_fields=[User.email, User.display_name, User.username],
            sortable_fields=[User.email, User.display_name, User.joined_at, User.status],
            page_size=25,
        )
    )

    admin.add_view(
        ModelView(
            UserFinance,
            icon="fa fa-money",
            label="Финансы",
            column_list=[UserFinance.user_id, UserFinance.income, UserFinance.housing, UserFinance.capital],
            page_size=25,
        )
    )

    admin.add_view(
        ModelView(
            Set,
            icon="fa fa-th-large",
            label="Наборы",
            column_list=[
                Set.id,
                Set.title,
                Set.source,
                Set.category_id,
                Set.users_count,
                Set.is_private,
                Set.created_at,
            ],
            searchable_fields=[Set.title],
            sortable_fields=[Set.title, Set.created_at, Set.users_count],
            page_size=25,
        )
    )

    admin.add_view(
        ModelView(
            Article,
            icon="fa fa-file-text",
            label="Статьи",
            column_list=[
                Article.id,
                Article.title,
                Article.status,
                Article.is_private,
                Article.views_count,
                Article.created_at,
            ],
            searchable_fields=[Article.title],
            sortable_fields=[Article.title, Article.created_at, Article.views_count],
            page_size=25,
        )
    )

    admin.add_view(
        ModelView(
            Deposit,
            icon="fa fa-bank",
            label="Вклады",
            column_list=[Deposit.id, Deposit.bank_name, Deposit.name, Deposit.freq, Deposit.is_active],
            searchable_fields=[Deposit.bank_name, Deposit.name],
            page_size=25,
        )
    )

    admin.add_view(
        ModelView(
            Card,
            icon="fa fa-credit-card",
            label="Карты",
            column_list=[Card.id, Card.bank_name, Card.name, Card.card_type, Card.is_active],
            searchable_fields=[Card.bank_name, Card.name],
            page_size=25,
        )
    )

    admin.add_view(
        ModelView(
            Company,
            icon="fa fa-building",
            label="Компании",
            column_list=[Company.id, Company.name, Company.category_id, Company.is_active],
            searchable_fields=[Company.name],
            page_size=25,
        )
    )

    admin.add_view(
        ModelView(
            Promo,
            icon="fa fa-tag",
            label="Промо",
            column_list=[
                Promo.id,
                Promo.type,
                Promo.title,
                Promo.company_id,
                Promo.votes_up,
                Promo.votes_down,
                Promo.is_active,
            ],
            searchable_fields=[Promo.title, Promo.text],
            page_size=25,
        )
    )

    admin.add_view(
        ModelView(
            Notification,
            icon="fa fa-bell",
            label="Уведомления",
            column_list=[
                Notification.id,
                Notification.user_id,
                Notification.type,
                Notification.title,
                Notification.is_read,
            ],
            page_size=25,
        )
    )

    admin.mount_to(app)
