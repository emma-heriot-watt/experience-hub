from typing import Optional

from opentelemetry import trace

from emma_common.datamodels import DialogueUtterance, EnvironmentStateTurn
from emma_experience_hub.api.clients.emma_policy import EmmaPolicyClient


tracer = trace.get_tracer(__name__)


class SimbotActionPredictionClient(EmmaPolicyClient):
    """Action prediction client which interfaces with the Policy model."""

    def generate(
        self,
        environment_state_history: list[EnvironmentStateTurn],
        dialogue_history: list[DialogueUtterance],
    ) -> str:
        """Generate a response from the features and provided language."""
        with tracer.start_as_current_span("Generate action"):
            return self._make_request(
                f"{self._endpoint}/generate", environment_state_history, dialogue_history
            )

    def find_object_in_scene(
        self,
        environment_state_history: list[EnvironmentStateTurn],
        dialogue_history: list[DialogueUtterance],
    ) -> list[str]:
        """Generate a response from the features and provided language."""
        with tracer.start_as_current_span("Find object in scene"):
            return self._make_request(
                f"{self._endpoint}/generate_find", environment_state_history, dialogue_history
            )

    def find_entity_from_history(
        self,
        environment_state_history: list[EnvironmentStateTurn],
        dialogue_history: list[DialogueUtterance],
    ) -> Optional[int]:
        """Try to find the entity in the given turns."""
        with tracer.start_as_current_span("Find Entity From History"):
            return self._make_request(
                f"{self._endpoint}/grab_from_history", environment_state_history, dialogue_history
            )
