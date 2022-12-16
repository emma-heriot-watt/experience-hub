import httpx
from loguru import logger
from pydantic import AnyHttpUrl

from emma_experience_hub.api.clients.client import Client


class ConfirmationResponseClassifierClient(Client):
    """Client for the confirmation response classifier."""

    def __init__(self, endpoint: AnyHttpUrl) -> None:
        self._endpoint = endpoint
        self._healthcheck_endpoint = f"{self._endpoint}/healthcheck"
        self._is_confirmation_endpoint = f"{self._endpoint}/is-confirmation"

    def healthcheck(self) -> bool:
        """Verify the server is healthy."""
        return self._run_healthcheck(self._healthcheck_endpoint)

    def is_confirmation(self, text: str) -> bool:
        """Return True if the input is a confirmation to the request."""
        response = httpx.post(self._is_confirmation_endpoint, params={"text": text})

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception(
                "Unable to detect whether utterance is a confirmation response", exc_info=err
            )
            raise err from None

        return response.json()
