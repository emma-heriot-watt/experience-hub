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
