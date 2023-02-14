from typing import Optional

from emma_experience_hub.datamodels.simbot import (
    SimBotEnvironmentIntentType,
    SimBotIntent,
    SimBotSession,
)
from emma_experience_hub.parsers.simbot import SimBotIntentFromActionStatusParser


class SimBotEnvironmentIntentExtractionPipeline:
    """Convert state information to help the agent know what to do."""

    def __init__(self) -> None:
        self._intent_from_action_status_parser = SimBotIntentFromActionStatusParser()

    def run(self, session: SimBotSession) -> Optional[SimBotIntent[SimBotEnvironmentIntentType]]:
        """Process environment state changes to inform the agent of its standing in the world."""
        # Return None if there is no previous turn or we got a new user utterance
        if not session.previous_turn or session.current_turn.speech is not None:
            return None

        # If we received no action statuses, do nothing and return
        intent = self._intent_from_action_status_parser(session.previous_turn)

        if intent is not None and intent.type.is_environment_error:
            session.current_state.utterance_queue.reset()
            session.current_state.find_queue.reset()
        # TODO: Add ways to handle other environment-based intents here

        return intent
