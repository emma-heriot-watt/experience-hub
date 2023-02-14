from typing import Optional

import httpx
from loguru import logger
from methodtools import lru_cache
from opentelemetry import trace

from emma_experience_hub.api.clients import Client


tracer = trace.get_tracer(__name__)

LRU_CACHE_MAX_SIZE = 64


class SimBotHacksClient(Client):
    """Client to access the SimBot Hacks service."""

    def healthcheck(self) -> bool:
        """Verify the server is healthy."""
        return self._run_healthcheck(f"{self._endpoint}/healthcheck")

    def get_low_level_prediction_from_raw_text(self, utterance: str) -> Optional[str]:
        """Generate a response from the features and provided language."""
        with tracer.start_as_current_span("Match text to template"):
            response = self._get_low_level_prediction_from_raw_text(utterance)

        logger.debug(f"Cache info: {self._get_low_level_prediction_from_raw_text.cache_info()}")
        return response

    @lru_cache(maxsize=LRU_CACHE_MAX_SIZE)  # noqa: B019
    def _get_low_level_prediction_from_raw_text(self, utterance: str) -> Optional[str]:
        """Generate a response from the features and provided language."""
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                f"{self._endpoint}/generate_raw_text_match", json={"text": utterance}
            )

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.warning("Unable to get an action from the raw text.", exc_info=err)
            return None

        return response.json()
