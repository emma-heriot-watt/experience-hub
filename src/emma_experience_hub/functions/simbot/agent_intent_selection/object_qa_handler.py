from typing import Optional

from emma_experience_hub.api.clients.simbot import SimBotQAIntentClient
from emma_experience_hub.datamodels.simbot import SimBotAgentIntents, SimBotSession
from emma_experience_hub.parsers.simbot import SimBotQAEntityParser


class SimBotObjectQAHandler:
    """Determine the agent intents from user intent QA."""

    def __init__(
        self, simbot_qa_client: SimBotQAIntentClient, simbot_qa_entity_parser: SimBotQAEntityParser
    ) -> None:
        self._simbot_qa_client = simbot_qa_client
        self._simbot_qa_entity_parser = simbot_qa_entity_parser

    def run(self, session: SimBotSession) -> Optional[SimBotAgentIntents]:
        """Handle a object QA intent."""
        raw_user_qa_response = self._simbot_qa_client.process_utterance(
            session.current_turn.speech.original_utterance.utterance
        )
        user_qa_intent_entity = self._simbot_qa_entity_parser(raw_user_qa_response)

        if user_qa_intent_entity is None or not user_qa_intent_entity.type.is_user_qa_about_object:
            raise AssertionError("User intent should be Object QA!")

        return SimBotAgentIntents(verbal_interaction=user_qa_intent_entity)
