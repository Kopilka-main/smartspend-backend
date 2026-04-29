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

    admin.add_view(ModelView(User, icon="fa fa-users", label="Пользователи"))
    admin.add_view(ModelView(UserFinance, icon="fa fa-money", label="Финансы"))
    admin.add_view(ModelView(Set, icon="fa fa-th-large", label="Наборы"))
    admin.add_view(ModelView(Article, icon="fa fa-file-text", label="Статьи"))
    admin.add_view(ModelView(Deposit, icon="fa fa-bank", label="Вклады"))
    admin.add_view(ModelView(Card, icon="fa fa-credit-card", label="Карты"))
    admin.add_view(ModelView(Company, icon="fa fa-building", label="Компании"))
    admin.add_view(ModelView(Promo, icon="fa fa-tag", label="Промо"))
    admin.add_view(ModelView(Notification, icon="fa fa-bell", label="Уведомления"))

    admin.mount_to(app)
