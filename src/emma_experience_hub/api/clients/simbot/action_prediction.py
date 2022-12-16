from typing import Optional

from loguru import logger
from methodtools import lru_cache

from emma_experience_hub.api.clients.emma_policy import EmmaPolicyClient
from emma_experience_hub.datamodels import DialogueUtterance, EnvironmentStateTurn


LRU_CACHE_MAX_SIZE = 64


class SimbotActionPredictionClient(EmmaPolicyClient):
    """Action prediction client which interfaces with the Policy model."""

    def find_object_in_scene(
        self,
        environment_state_history: list[EnvironmentStateTurn],
        dialogue_history: list[DialogueUtterance],
    ) -> list[str]:
        """Generate a response from the features and provided language."""
        return self._make_request(
            f"{self._endpoint}/generate_find", environment_state_history, dialogue_history
        )

    def get_low_level_prediction_from_raw_text(
        self,
        environment_state_history: list[EnvironmentStateTurn],
        dialogue_history: list[DialogueUtterance],
    ) -> Optional[str]:
        """Generate a response from the features and provided language."""
        response = self._get_low_level_prediction_from_raw_text(
            tuple(environment_state_history), tuple(dialogue_history)
        )
        logger.debug(f"Cache info: {self._get_low_level_prediction_from_raw_text.cache_info()}.")
        return response

    @lru_cache(maxsize=LRU_CACHE_MAX_SIZE)  # noqa: B019
    def _get_low_level_prediction_from_raw_text(
        self,
        environment_state_history: tuple[EnvironmentStateTurn],
        dialogue_history: tuple[DialogueUtterance],
    ) -> Optional[str]:
        """Generate a response from the features and provided language."""
        return self._make_request(
            f"{self._endpoint}/generate_raw_text_match",
            list(environment_state_history),
            list(dialogue_history),
        )
