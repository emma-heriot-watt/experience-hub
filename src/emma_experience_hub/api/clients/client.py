from abc import ABC, abstractmethod
from typing import Optional

import httpx
from loguru import logger
from pydantic import AnyHttpUrl


class Client(ABC):
    """Base client for all the API clients."""

    def __init__(
        self, endpoint: AnyHttpUrl, timeout: Optional[int], *, disable: bool = False
    ) -> None:
        self._endpoint = endpoint
        self._timeout = timeout

        self._is_disabled = disable

    @abstractmethod
    def healthcheck(self) -> bool:
        """Verify that the client is running and healthy."""
        raise NotImplementedError()

    def _run_healthcheck(self, endpoint: str) -> bool:
        """Verify the server is healthy."""
        if self._is_disabled:
            logger.debug(f"Client disabled for {self.__class__.__name__}")
            return True

        with httpx.Client() as client:
            response = client.get(endpoint)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            logger.exception("Unable to perform healthcheck")
            return False

        return True
