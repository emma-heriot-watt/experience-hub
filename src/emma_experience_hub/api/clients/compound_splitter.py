import httpx
from loguru import logger
from pydantic import AnyHttpUrl

from emma_experience_hub.api.clients.client import Client


class CompoundSplitterClient(Client):
    """Client for the compound splitter service."""

    def __init__(self, endpoint: AnyHttpUrl) -> None:
        self._endpoint = endpoint
        self._healthcheck_endpoint = f"{self._endpoint}/healthcheck"
        self._compound_splitter_endpoint = f"{self._endpoint}/split"

    def healthcheck(self) -> bool:
        """Verify the server is healthy."""
        response = httpx.get(self._healthcheck_endpoint)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            logger.exception(
                "Unable to perform healthcheck on confirmation classifier", exc_info=err
            )
            return False

        return True

    def split(self, instruction: str) -> list[str]:
        """Given a complex instruction, returns a list of simpler instructions."""
        response = httpx.post(self._compound_splitter_endpoint, json={"instruction": instruction})

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.warning(
                "Unable to split the utterance further due to an issue in the splitter. Using speech utterance as is.",
                exc_info=err,
            )
            return []

        return response.json()