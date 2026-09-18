import logging
from typing import Any, Optional
import librouteros
from librouteros.exceptions import LibRouterosError, TrapError

logger = logging.getLogger(__name__)


class MikrotikClient:
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 8728,
        use_ssl: bool = False,
        timeout: int = 5,
    ):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.use_ssl = use_ssl
        self.timeout = timeout
        self._api: Optional[Any] = None

    def connect(self):
        """Establish connection to MikroTik RouterOS API."""
        try:
            self._api = librouteros.connect(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                ssl=self.use_ssl,
                timeout=self.timeout,
            )
            return self._api
        except Exception as exc:
            logger.error(f"Failed to connect to MikroTik at {self.host}:{self.port} - {exc}")
            raise ConnectionError(f"Gagal terhubung ke MikroTik ({self.host}:{self.port}): {str(exc)}")

    @property
    def api(self):
        if self._api is None:
            self.connect()
        return self._api

    def close(self):
        """Close connection."""
        if self._api is not None:
            try:
                self._api.close()
            except Exception:
                pass
            finally:
                self._api = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
