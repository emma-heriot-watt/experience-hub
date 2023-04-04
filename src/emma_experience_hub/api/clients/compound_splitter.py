from typing import Optional

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
        except httpx.HTTPError:
            logger.warning(
                "Unable to split the utterance further due to an issue in the splitter. Using speech utterance as is.",
            )
            return []

        return response.json()

    def high_level_plan(self, instruction: str, inventory_entity: Optional[str]) -> list[str]:
        """Given a complex instruction, returns a list of simpler instructions."""
        with httpx.Client(timeout=None) as client:
            response = client.post(
                f"{self._endpoint}/high_level_planner",
                json={"instruction": instruction, "inventory_entity": inventory_entity},
            )
        try:
            response.raise_for_status()
        except httpx.HTTPError:
            logger.exception(
                "Unable to split the utterance using the high-level planner. Using speech utterance as is."
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
        except httpx.HTTPError:
            logger.exception("Unable to perform coreference resolution.")
            return instructions[-1]

        return response.json()
