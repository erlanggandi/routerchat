from fastapi import APIRouter
from app.api.v1.routers import router as routers_router
from app.api.v1.monitoring import router as monitoring_router
from app.api.v1.chat import router as chat_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.telegram import router as telegram_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(routers_router)
api_v1_router.include_router(monitoring_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(approvals_router)
api_v1_router.include_router(telegram_router)
