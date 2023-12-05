from typing import Optional

from emma_common.datamodels import DialogueUtterance, EnvironmentStateTurn
from emma_experience_hub.api.clients.emma_policy import EmmaPolicyClient


class SimbotActionPredictionClient(EmmaPolicyClient):
    """Action prediction client which interfaces with the Policy model."""

    def generate(
        self,
        environment_state_history: list[EnvironmentStateTurn],
        dialogue_history: list[DialogueUtterance],
        force_stop_token: bool = False,
        inventory_entity: Optional[str] = None,
    ) -> str:
        """Generate a response from the features and provided language."""
        return self._make_request(
            f"{self._endpoint}/generate",
            environment_state_history,
            dialogue_history,
            force_stop_token=force_stop_token,
            inventory_entity=inventory_entity,
        )

    def find_object_in_scene(
        self,
        environment_state_history: list[EnvironmentStateTurn],
        dialogue_history: list[DialogueUtterance],
        inventory_entity: Optional[str] = None,
    ) -> list[str]:
        """Generate a response from the features and provided language."""
        return self._make_request(
            f"{self._endpoint}/generate_find",
            environment_state_history,
            dialogue_history,
            inventory_entity=inventory_entity,
        )
