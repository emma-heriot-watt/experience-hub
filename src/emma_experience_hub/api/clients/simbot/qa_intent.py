from typing import Any, Optional

import httpx
from loguru import logger
from methodtools import lru_cache

from emma_experience_hub.api.clients.client import Client


LRU_CACHE_MAX_SIZE = 64


class SimBotQAIntentClient(Client):
    """Client for the QA Intent service."""

    def healthcheck(self) -> bool:
        """Verify the server is healthy."""
        return self._run_healthcheck(f"{self._endpoint}")

    def process_utterance(self, utterance: str) -> Optional[dict[str, Any]]:
        """Given an utterance extract intents and entities."""
        response = self._process_utterance(utterance)

        logger.debug(f"Cache info: {self._process_utterance.cache_info()}")
        return response

    @lru_cache(maxsize=LRU_CACHE_MAX_SIZE)  # noqa: B019
    def _process_utterance(self, utterance: str) -> Optional[dict[str, Any]]:
        """Given an utterance extract intents and entities."""
        with httpx.Client(timeout=None) as client:
            response = client.post(
                f"{self._endpoint}/model/parse", json={"text": utterance.lower()}
            )

        try:
            response.raise_for_status()
        except httpx.HTTPError:
            logger.exception("Unable to process utterance with QA client.")
            return None

        response_json = response.json()

        # If the intent key does not exist, we don't have an intent
        if "intent" not in response_json.keys():
            logger.warning(f"There is no `intent` key within the response: {response_json}")
            return None

        return response_json
