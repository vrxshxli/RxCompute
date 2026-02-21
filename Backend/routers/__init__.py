from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.medicines import router as medicines_router
from routers.orders import router as orders_router
from routers.notifications import router as notifications_router

__all__ = [
    "auth_router",
    "users_router",
    "medicines_router",
    "orders_router",
    "notifications_router",
]
