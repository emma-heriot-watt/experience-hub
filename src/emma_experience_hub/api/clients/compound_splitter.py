import httpx
from loguru import logger

from emma_experience_hub.api.clients.client import Client


class CompoundSplitterClient(Client):
    """Client for the compound splitter service."""

    def healthcheck(self) -> bool:
        """Verify the server is healthy."""
        return self._run_healthcheck(f"{self._endpoint}/healthcheck")

    def split(self, instruction: str) -> list[str]:
        """Given a complex instruction, returns a list of simpler instructions."""
        with httpx.Client(timeout=None) as client:
            response = client.post(f"{self._endpoint}/split", json={"instruction": instruction})

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.warning(
                "Unable to split the utterance further due to an issue in the splitter. Using speech utterance as is.",
                exc_info=err,
            )
            return []

        return response.json()

    def resolve_coreferences(self, instructions: list[str]) -> str:
        """Resolve coreferences."""
        with httpx.Client(timeout=None) as client:
            response = client.post(
                f"{self._endpoint}/coreference_resolution", json={"instructions": instructions}
            )

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.warning("Unable to perform coreference resolution.", exc_info=err)
            return instructions[-1]

        return response.json()
