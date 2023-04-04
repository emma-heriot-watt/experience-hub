import httpx
from loguru import logger

from emma_experience_hub.api.clients.client import Client


class ProfanityFilterClient(Client):
    """Client for the profanity filter."""

    def healthcheck(self) -> bool:
        """Verify the profanity filter server is healthy."""
        return self._run_healthcheck(f"{self._endpoint}/healthcheck")

    def is_profane(self, text: str) -> bool:
        """Return True if the input is profane."""
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(f"{self._endpoint}/is-profane", json={"text": text})

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception("Unable to detect whether utterance is profane")
            raise err from None

        return response.json()
