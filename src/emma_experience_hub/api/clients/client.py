from abc import ABC, abstractmethod


class Client(ABC):
    """Base client for all the API clients."""

    @abstractmethod
    def healthcheck(self) -> bool:
        """Verify that the client is running and healthy."""
        raise NotImplementedError()
