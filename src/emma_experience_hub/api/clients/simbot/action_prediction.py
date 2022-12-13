from typing import Optional

from emma_experience_hub.api.clients.emma_policy import EmmaPolicyClient
from emma_experience_hub.datamodels import DialogueUtterance, EnvironmentStateTurn


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
        return self._make_request(
            f"{self._endpoint}/generate_raw_text_match",
            environment_state_history,
            dialogue_history,
        )
