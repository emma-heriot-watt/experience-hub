from typing import Optional

from emma_common.datamodels import DialogueUtterance, EnvironmentStateTurn
from emma_experience_hub.api.clients.emma_policy import EmmaPolicyClient


class SimBotCRIntentClient(EmmaPolicyClient):
    """API Client for SimBot CR."""

    def generate(
        self,
        environment_state_history: list[EnvironmentStateTurn],
        dialogue_history: list[DialogueUtterance],
        inventory_entity: Optional[str] = None,
    ) -> str:
        """Generate a response from the features and provided language."""
        return self._make_request(
            f"{self._endpoint}/generate",
            environment_state_history,
            dialogue_history,
            inventory_entity,
        )
