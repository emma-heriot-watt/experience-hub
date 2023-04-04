from typing import Optional

import httpx
from loguru import logger

from emma_experience_hub.api.clients.client import Client


class ConfirmationResponseClassifierClient(Client):
    """Client for the confirmation response classifier."""

    def healthcheck(self) -> bool:
        """Verify the server is healthy."""
        return self._run_healthcheck(f"{self._endpoint}/healthcheck")

    def is_request_approved(self, text: str) -> Optional[bool]:
        """Return boolean to the incoming request, or None if it is not a confirmation request."""
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(f"{self._endpoint}/is-confirmation", params={"text": text})

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception("Unable to detect whether utterance is a confirmation response")
            raise err from None

        return response.json()
