import httpx
from loguru import logger
from pydantic import AnyHttpUrl

from emma_experience_hub.api.clients.client import Client


class ProfanityFilterClient(Client):
    """Client for the profanity filter."""

    def __init__(self, endpoint: AnyHttpUrl) -> None:
        self._endpoint = endpoint
        self._healthcheck_endpoint = f"{self._endpoint}/healthcheck"
        self._is_profane_endpoint = f"{self._endpoint}/is-profane"

    def healthcheck(self) -> bool:
        """Verify the profanity filter server is healthy."""
        return self._run_healthcheck(self._healthcheck_endpoint)

    def is_profane(self, text: str) -> bool:
        """Return True if the input is profane."""
        with httpx.Client() as client:
            response = client.post(self._is_profane_endpoint, json={"text": text})

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception("Unable to detect whether utterance is profane", exc_info=err)
            raise err from None

        return response.json()
