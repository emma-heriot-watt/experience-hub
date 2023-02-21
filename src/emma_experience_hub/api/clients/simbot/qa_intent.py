from typing import Any, Optional

import httpx
from loguru import logger

from emma_experience_hub.api.clients.client import Client


class SimBotQAIntentClient(Client):
    """Client for the QA Intent service."""

    def healthcheck(self) -> bool:
        """Verify the server is healthy."""
        return self._run_healthcheck(f"{self._endpoint}")

    def process_utterance(self, utterance: str) -> Optional[dict[str, Any]]:
        """Given an utterance extract intents and entities."""
        with httpx.Client(timeout=None) as client:
            response = client.post(
                f"{self._endpoint}/model/parse", json={"text": utterance.lower()}
            )

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.warning(
                "Unable to process utterance with QA client.",
                exc_info=err,
            )
            return None

        response_json = response.json()

        # If the intent key does not exist, we don't have an intent
        if "intent" not in response_json.keys():
            logger.warning(f"There is no `intent` key within the response: {response_json}")
            return None

        return response_json
