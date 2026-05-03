from fastapi import APIRouter

from src.app.api.v1.articles import router as articles_router
from src.app.api.v1.auth import router as auth_router
from src.app.api.v1.cards import router as cards_router
from src.app.api.v1.catalog import router as catalog_router
from src.app.api.v1.companies import router as companies_router
from src.app.api.v1.deposits import router as deposits_router
from src.app.api.v1.envelopes import router as envelopes_router
from src.app.api.v1.feed import router as feed_router
from src.app.api.v1.follows import router as follows_router
from src.app.api.v1.inventory import router as inventory_router
from src.app.api.v1.notifications import router as notifications_router
from src.app.api.v1.promos import router as promos_router
from src.app.api.v1.reactions import router as reactions_router
from src.app.api.v1.reference import router as reference_router
from src.app.api.v1.uploads import router as uploads_router
from src.app.api.v1.users import router as users_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(catalog_router)
api_router.include_router(articles_router)
api_router.include_router(inventory_router)
api_router.include_router(envelopes_router)
api_router.include_router(feed_router)
api_router.include_router(follows_router)
api_router.include_router(reactions_router)
api_router.include_router(notifications_router)
api_router.include_router(reference_router)
api_router.include_router(deposits_router)
api_router.include_router(cards_router)
api_router.include_router(companies_router)
api_router.include_router(promos_router)
api_router.include_router(uploads_router)
