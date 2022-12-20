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
        return self._run_healthcheck(self._healthcheck_endpoint)

    def split(self, instruction: str) -> list[str]:
        """Given a complex instruction, returns a list of simpler instructions."""
        with httpx.Client() as client:
            response = client.post(
                self._compound_splitter_endpoint, json={"instruction": instruction}
            )

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.warning(
                "Unable to split the utterance further due to an issue in the splitter. Using speech utterance as is.",
                exc_info=err,
            )
            return []

        return response.json()
