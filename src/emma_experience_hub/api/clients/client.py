from abc import ABC, abstractmethod

import httpx
from loguru import logger


class Client(ABC):
    """Base client for all the API clients."""

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
        except httpx.HTTPStatusError as err:
            logger.exception("Unable to perform healthcheck", exc_info=err)
            return False

        return True
