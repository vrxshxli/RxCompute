from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.medicines import router as medicines_router
from routers.orders import router as orders_router
from routers.notifications import router as notifications_router
from routers.user_medications import router as user_medications_router
from routers.home import router as home_router
from routers.chat import router as chat_router
from routers.jobs import router as jobs_router
from routers.webhooks import router as webhooks_router
from routers.pharmacy_stores import router as pharmacy_stores_router
from routers.warehouse import router as warehouse_router
from routers.safety import router as safety_router
from routers.scheduler import router as scheduler_router
from routers.predictions import router as predictions_router

__all__ = [
    "auth_router",
    "users_router",
    "medicines_router",
    "orders_router",
    "notifications_router",
    "user_medications_router",
    "home_router",
    "chat_router",
    "jobs_router",
    "webhooks_router",
    "pharmacy_stores_router",
    "warehouse_router",
    "safety_router",
    "scheduler_router",
    "predictions_router",
]
