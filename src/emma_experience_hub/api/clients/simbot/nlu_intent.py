from opentelemetry import trace

from emma_common.datamodels import DialogueUtterance, EnvironmentStateTurn
from emma_experience_hub.api.clients.emma_policy import EmmaPolicyClient


tracer = trace.get_tracer(__name__)


class SimBotNLUIntentClient(EmmaPolicyClient):
    """API Client for SimBot NLU."""

    def generate(
        self,
        environment_state_history: list[EnvironmentStateTurn],
        dialogue_history: list[DialogueUtterance],
    ) -> str:
        """Generate a response from the features and provided language."""
        with tracer.start_as_current_span("Generate NLU intent"):
            return self._make_request(
                f"{self._endpoint}/generate", environment_state_history, dialogue_history
            )
