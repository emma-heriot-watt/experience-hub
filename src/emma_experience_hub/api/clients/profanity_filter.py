import httpx
from pydantic import AnyHttpUrl

from emma_experience_hub.api.clients.client import Client
from emma_experience_hub.common.logging import get_logger


logger = get_logger("profanity_filter_client")


class ProfanityFilterClient(Client):
    """Client for the profanity filter."""

    def __init__(self, endpoint: AnyHttpUrl) -> None:
        self._endpoint = endpoint
        self._healthcheck_endpoint = f"{self._endpoint}/healthcheck"
        self._is_profane_endpoint = f"{self._endpoint}/is-profane"

    def healthcheck(self) -> bool:
        """Verify the profanity filter server is healthy."""
        response = httpx.get(self._healthcheck_endpoint)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            logger.exception(err, exc_info=err)
            return False

        return True

    def is_profane(self, text: str) -> bool:
        """Return True if the input is profane."""
        response = httpx.post(self._is_profane_endpoint, json={"text": text})

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception(err, exc_info=err)
            raise err from None

        return response.json()
