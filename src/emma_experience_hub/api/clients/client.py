from abc import ABC, abstractmethod
from typing import Optional

import httpx
from loguru import logger
from pydantic import AnyHttpUrl


class Client(ABC):
    """Base client for all the API clients."""

    def __init__(self, endpoint: AnyHttpUrl, timeout: Optional[int]) -> None:
        self._endpoint = endpoint
        self._timeout = timeout

    @abstractmethod
    def healthcheck(self) -> bool:
        """Verify that the client is running and healthy."""
        raise NotImplementedError()

    def _run_healthcheck(self, endpoint: str) -> bool:
        """Verify the server is healthy."""
        with httpx.Client() as client:
            response = client.get(endpoint)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            logger.exception("Unable to perform healthcheck")
            return False

        return True
