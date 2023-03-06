from loguru import logger
from opentelemetry import trace

from emma_experience_hub.api.clients.simbot import SimBotHacksClient
from emma_experience_hub.datamodels.simbot import SimBotIntent, SimBotIntentType, SimBotSession


tracer = trace.get_tracer(__name__)


class SimbotAnticipatorPipeline:
    """Generate a plan of instructions and appends them to the utterance queue."""

    def __init__(self, simbot_hacks_client: SimBotHacksClient) -> None:
        self._simbot_hacks_client = simbot_hacks_client

    def run(self, session: SimBotSession) -> None:
        """Generate an action to perform on the environment."""
        # Do not run the anticipator pipeline if there are utterances in queue.
        # We dont want to add the utterances produced by the anticipator if
        # 1) the previous utterance has been split by the compound splitter, meaning there are still actions that the user asked us to perform or
        # 2) in some previous turn the anticipator produced already a plan that are now executing, therefore we dont want to override that plan.
        if session.current_state.utterance_queue.is_not_empty:
            return

        current_action = session.current_turn.actions.interaction
        if current_action is not None:
            anticipator_output = self._simbot_hacks_client.get_anticipator_prediction_from_action(
                action=current_action,
                inventory_entity=session.current_turn.state.inventory.entity,
            )

            # If the anticipator has returned a sequence of instructions update the utterance queue
            if anticipator_output is None:
                return

            logger.debug(
                f"[Plan] Adding the plan utterances to the queue: {anticipator_output.utterances}"
            )
            session.current_state.utterance_queue.reset()
            session.current_state.utterance_queue.extend_tail(anticipator_output.utterances)

            # We also need to update the verbal interaction intent to confirm in order to
            # get the confirmation from the user in the next turn
            session.current_turn.intent.verbal_interaction = SimBotIntent(
                type=SimBotIntentType.confirm_before_plan
            )
