import httpx
from loguru import logger

from emma_experience_hub.api.clients.client import Client


class ConfirmationResponseClassifierClient(Client):
    """Client for the confirmation response classifier."""

    def healthcheck(self) -> bool:
        """Verify the server is healthy."""
        return self._run_healthcheck(f"{self._endpoint}/healthcheck")

    def is_confirmation(self, text: str) -> bool:
        """Return True if the input is a confirmation to the request."""
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(f"{self._endpoint}/is-confirmation", params={"text": text})

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception(
                "Unable to detect whether utterance is a confirmation response", exc_info=err
            )
            raise err from None

        return response.json()
