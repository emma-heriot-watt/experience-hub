from typing import Optional

from emma_common.datamodels import SpeakerRole
from emma_experience_hub.api.clients.simbot import SimBotQAIntentClient
from emma_experience_hub.datamodels.simbot import (
    SimBotAgentIntents,
    SimBotAnyUserIntentType,
    SimBotIntent,
    SimBotIntentType,
    SimBotSession,
    SimBotUserSpeech,
)
from emma_experience_hub.parsers.simbot import SimBotQAEntityParser


class SimBotObjectQAHandler:
    """Determine the agent intents from user intent QA."""

    def __init__(
        self,
        simbot_qa_client: SimBotQAIntentClient,
        simbot_qa_entity_parser: SimBotQAEntityParser,
        _enable_confirmation_questions: bool = True,
    ) -> None:
        self._simbot_qa_client = simbot_qa_client
        self._simbot_qa_entity_parser = simbot_qa_entity_parser
        self._enable_confirmation_questions = _enable_confirmation_questions

    def run(self, session: SimBotSession) -> Optional[SimBotAgentIntents]:
        """Handle a object QA intent."""
        if session.current_turn.speech is None:
            return None
        raw_user_qa_response = self._simbot_qa_client.process_utterance(
            session.current_turn.speech.original_utterance.utterance
        )
        if raw_user_qa_response is None:
            return None

        user_qa_intent = self._simbot_qa_entity_parser(raw_user_qa_response)

        if user_qa_intent is None or not user_qa_intent.type.is_user_qa_about_object:
            raise AssertionError("User intent should be Object QA!")

        if user_qa_intent.type == SimBotIntentType.ask_about_location:
            return self._handle_ask_about_location(session, user_qa_intent)

        return SimBotAgentIntents(verbal_interaction=user_qa_intent)  # type: ignore[arg-type]

    def _has_seen_object(self, session: SimBotSession, target_entity: str) -> bool:
        """Has the agent seen the entity."""
        # we've seen the entity in the current room or know its location from prior memory
        has_seen_object = session.current_state.memory.object_in_memory(
            target_entity, current_room=session.current_turn.environment.current_room
        )
        return has_seen_object

    def _handle_in_memory_entities(
        self, session: SimBotSession, target_entity: str
    ) -> SimBotAgentIntents:
        """Update the session if the object is in memory .

        When object is seen and start a search. Current utterance will NOT be queued.
        """
        session.current_turn.speech = SimBotUserSpeech.update_user_utterance(
            utterance=f"find the {target_entity}",
            role=SpeakerRole.agent,
            original_utterance=session.current_turn.speech.original_utterance
            if session.current_turn.speech is not None
            else None,
        )
        return SimBotAgentIntents(
            SimBotIntent(type=SimBotIntentType.search, entity=target_entity),
            SimBotIntent(
                type=SimBotIntentType.act_no_match,
                entity=target_entity,
            ),
        )

    def _is_searching_for_hodling_object(self, session: SimBotSession, target_entity: str) -> bool:
        holding_object = session.inventory.entity
        if holding_object and holding_object.lower() == target_entity:  # noqa: WPS531
            return True
        return False

    def _handle_searching_holding_object(
        self, session: SimBotSession, target_entity: str
    ) -> SimBotAgentIntents:
        # If searching for the holding object, assing an already_holding_object error
        session.current_turn.intent.environment = SimBotIntent(
            type=SimBotIntentType.already_holding_object, entity=target_entity
        )
        return SimBotAgentIntents()

    def _handle_search_after_ask_about_location(self, target_entity: str) -> SimBotAgentIntents:
        """Search after asking about location."""
        if not self._enable_confirmation_questions:
            return SimBotAgentIntents(
                verbal_interaction=SimBotIntent(
                    type=SimBotIntentType.ask_about_location, entity=target_entity
                )
            )
        return SimBotAgentIntents(
            verbal_interaction=SimBotIntent(
                type=SimBotIntentType.confirm_before_search, entity=target_entity
            ),
        )

    def _handle_ask_about_location(
        self, session: SimBotSession, user_qa_intent: SimBotIntent[SimBotAnyUserIntentType]
    ) -> SimBotAgentIntents:
        user_intent_entity = user_qa_intent.entity
        if user_intent_entity is None:
            return SimBotAgentIntents(
                verbal_interaction=SimBotIntent(type=SimBotIntentType.ask_about_location),
            )

        # If the user is asking for the object we are holding, say we are holding it
        if self._is_searching_for_hodling_object(session, user_intent_entity):
            return self._handle_searching_holding_object(session, user_intent_entity)

        # If we have seen the object, search for it
        if self._has_seen_object(session, user_intent_entity):
            return self._handle_in_memory_entities(session, user_intent_entity)

        # Otherwise respond
        return SimBotAgentIntents(
            verbal_interaction=SimBotIntent(
                type=SimBotIntentType.ask_about_location, entity=user_intent_entity
            )
        )
