from typing import Optional

from emma_experience_hub.datamodels.simbot import SimBotIntent, SimBotSession
from emma_experience_hub.parsers.simbot import SimBotIntentFromActionStatusParser


class SimBotEnvironmentIntentExtractionPipeline:
    """Convert state information to help the agent know what to do."""

    def __init__(self) -> None:
        self._intent_from_action_status_parser = SimBotIntentFromActionStatusParser()

    def run(self, session: SimBotSession) -> Optional[SimBotIntent]:
        """Process environment state changes to inform the agent of its standing in the world."""
        # Return None if there is no previous turn
        if not session.previous_turn:
            return None

        # If we received no action statuses, do nothing and return
        intent = self._intent_from_action_status_parser(session.previous_turn)

        # TODO: Add ways to handle other environment-based intents here

        return intent
