import logging
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.mikrotik.client import MikrotikClient
from app.mikrotik.service import MikrotikService
from app.database.models import Router
from app.database import crud
from app.utils.security import decrypt_secret

logger = logging.getLogger(__name__)


class RouterManager:
    """Manages multi-router connections, instances, and user active router resolution."""

    def __init__(self):
        self._cached_services: Dict[int, MikrotikService] = {}

    def get_service_for_router(self, router: Router) -> MikrotikService:
        """Create or reuse MikrotikService for a given router."""
        password = decrypt_secret(router.password_encrypted)
        client = MikrotikClient(
            host=router.host,
            username=router.username,
            password=password,
            port=router.port,
            use_ssl=router.use_ssl,
        )
        return MikrotikService(client)

    async def get_active_service_for_user(
        self, db: AsyncSession, user_id: int
    ) -> tuple[Optional[Router], Optional[MikrotikService]]:
        """Resolve active router and service for a Telegram user."""
        router = await crud.get_active_router_for_user(db, user_id)
        if not router:
            return None, None
        service = self.get_service_for_router(router)
        return router, service


router_manager = RouterManager()
