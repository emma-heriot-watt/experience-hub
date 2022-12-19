import httpx
from loguru import logger
from pydantic import AnyHttpUrl

from emma_experience_hub.api.clients.client import Client


class OutOfDomainDetectorClient(Client):
    """Detect whether a given text is out of the chosen domain."""

    def __init__(self, endpoint: AnyHttpUrl) -> None:
        self._endpoint = endpoint

    def healthcheck(self) -> bool:
        """Verify the server is healthy."""
        return self._run_healthcheck(f"{self._endpoint}/healthcheck")

    def is_out_of_domain(self, text: str) -> bool:
        """Return True if the input is out of the domain."""
        with httpx.Client() as client:
            response = client.post(f"{self._endpoint}/is-out-of-domain", params={"text": text})

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception("Failed to detect domain of text", exc_info=err)
            raise err from None

        return response.json()
