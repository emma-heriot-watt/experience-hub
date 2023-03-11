from typing import Optional

from emma_experience_hub.datamodels.simbot import (
    SimBotAgentIntents,
    SimBotIntent,
    SimBotIntentType,
    SimBotSession,
)


class SimBotClarificationHandler:
    """Determine the agent intents after a clarification."""

    def run(self, session: SimBotSession) -> Optional[SimBotAgentIntents]:
        """Get the agent intent."""
        return SimBotAgentIntents(
            physical_interaction=SimBotIntent(type=SimBotIntentType.act_one_match)
        )
