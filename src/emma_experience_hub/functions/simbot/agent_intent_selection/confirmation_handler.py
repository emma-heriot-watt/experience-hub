from typing import Optional

from emma_common.datamodels import SpeakerRole
from emma_experience_hub.datamodels.simbot import (
    SimBotAgentIntents,
    SimBotIntent,
    SimBotIntentType,
    SimBotSession,
    SimBotSessionTurn,
    SimBotUserIntentType,
    SimBotUserSpeech,
)
from emma_experience_hub.datamodels.simbot.queue import SimBotQueueUtterance


def set_find_object_in_progress_intent(session: SimBotSession) -> SimBotAgentIntents:
    """Set the intent when find is in progress."""
    if not session.previous_turn or session.previous_turn.intent.physical_interaction is None:
        return SimBotAgentIntents(SimBotIntent(type=SimBotIntentType.search))

    entity = session.previous_turn.intent.physical_interaction.entity
    previous_intent = session.previous_turn.intent
    # Retain the information that the search was triggered by an act_no_match or act_missing_inventory
    is_searching_inferred_object = (
        previous_intent.is_searching_inferred_object
        and not session.previous_turn.is_going_to_found_object_from_search
    )
    if is_searching_inferred_object and previous_intent.verbal_interaction is not None:
        return SimBotAgentIntents(
            SimBotIntent(type=SimBotIntentType.search, entity=entity),
            SimBotIntent(
                type=previous_intent.verbal_interaction.type,
                entity=entity,
            ),
        )
    return SimBotAgentIntents(SimBotIntent(type=SimBotIntentType.search, entity=entity))


class SimBotConfirmationHandler:
    """Determine the agent intents after a confirmation."""

    def __init__(
        self,
        _enable_search_after_no_match: bool = True,
    ) -> None:
        self._enable_search_after_no_match = _enable_search_after_no_match

    def run(self, session: SimBotSession) -> Optional[SimBotAgentIntents]:
        """Handle a confirmation intent."""
        user_intent = session.current_turn.intent.user
        if user_intent is None or not SimBotIntentType.is_user_intent_type(user_intent):
            raise AssertionError("User intent should not be None!")
        # If the agent asked for confirmation to search for an object required to act
        if self._agent_asked_for_confirm_before_searching(session, user_intent):
            return self._handle_confirm_before_search_intent(
                session=session, user_intent=user_intent
            )

        # If we are within a find routine AND received a confirmation response from the user
        if session.is_find_object_in_progress and user_intent.is_confirmation_response:
            # Then let the search routine decide how to handle it.
            return set_find_object_in_progress_intent(session)

        # If the agent explicitly asked a confirmation question before executing a plan in the previous turn
        if self._agent_asked_for_confirm_before_plan(session.previous_valid_turn):
            return self._handle_confirm_before_plan_intent(session, user_intent)

        # If the agent explicitly asked a confirmation question in the previous turn
        if self._agent_asked_for_confirm_before_acting(session.previous_valid_turn):
            return self._handle_confirm_before_previous_act_intent(session, user_intent)
        return SimBotAgentIntents()

    def _handle_confirm_before_previous_act_intent(
        self, session: SimBotSession, user_intent: SimBotUserIntentType
    ) -> SimBotAgentIntents:
        """Handle a confirmation to execute the previous action."""
        # If the user approved
        if user_intent == SimBotIntentType.confirm_yes:
            return SimBotAgentIntents(
                physical_interaction=SimBotIntent(type=SimBotIntentType.act_previous)
            )

        session.current_state.utterance_queue.reset()
        return SimBotAgentIntents()

    def _handle_confirm_before_search_intent(
        self, session: SimBotSession, user_intent: SimBotUserIntentType
    ) -> SimBotAgentIntents:
        """Handle a confirmation to search."""
        if user_intent != SimBotIntentType.confirm_yes:
            session.current_state.utterance_queue.reset()
            return SimBotAgentIntents()

        previous_turn = session.previous_turn
        if previous_turn is None or previous_turn.intent.verbal_interaction is None:
            raise AssertionError("User intent is confirmation without a previous verbal intent")

        # Do a search routine before executing the latest instruction.
        if not session.current_turn.speech.utterance.startswith("go to the"):  # type: ignore[union-attr]
            session.current_state.utterance_queue.append_to_head(
                SimBotQueueUtterance(
                    utterance=previous_turn.speech.utterance,  # type: ignore[union-attr]
                    role=previous_turn.speech.role,  # type: ignore[union-attr]
                ),
            )
        target_entity = previous_turn.intent.verbal_interaction.entity
        session.current_turn.speech = SimBotUserSpeech.update_user_utterance(
            utterance=f"find the {target_entity}",
            role=SpeakerRole.agent,
            original_utterance=session.current_turn.speech.original_utterance
            if session.current_turn.speech
            else None,
        )
        return SimBotAgentIntents(
            physical_interaction=SimBotIntent(type=SimBotIntentType.search, entity=target_entity),
            verbal_interaction=SimBotIntent(
                type=SimBotIntentType.act_no_match, entity=target_entity
            ),
        )

    def _handle_confirm_before_plan_intent(
        self, session: SimBotSession, user_intent: SimBotUserIntentType
    ) -> Optional[SimBotAgentIntents]:
        """Handle a confirmation to execute the plan."""
        # If the user approved
        if user_intent == SimBotIntentType.confirm_yes:
            # Pop the first element in the instruction plan and add it to the utterance speech
            queue_elem = session.current_state.utterance_queue.pop_from_head()
            session.current_turn.speech = SimBotUserSpeech.update_user_utterance(
                utterance=queue_elem.utterance,
                from_utterance_queue=True,
                role=queue_elem.role,
                original_utterance=session.current_turn.speech.original_utterance
                if session.current_turn.speech
                else None,
            )
            return None

        # If the user didn't approve
        session.current_state.utterance_queue.reset()
        return SimBotAgentIntents()

    def _agent_asked_for_confirm_before_acting(
        self, previous_turn: Optional[SimBotSessionTurn]
    ) -> bool:
        """Did the agent explicitly ask for confirmation before performing an action?"""
        return (
            previous_turn is not None
            and previous_turn.intent.verbal_interaction is not None
            and previous_turn.intent.verbal_interaction.type.triggers_confirmation_question
        )

    def _agent_asked_for_confirm_before_searching(
        self, session: SimBotSession, user_intent: SimBotUserIntentType
    ) -> bool:
        """Did the agent explicitly ask for confirmation before searching for an unseen object?"""
        if not self._enable_search_after_no_match:
            return False

        # Verify the user provided a confirmation response (Y/N)
        if not user_intent.is_confirmation_response or session.previous_turn is None:
            return False

        # Verify the previous turn outputted an `confirm_before_search`
        previous_verbal_intent = session.previous_turn.intent.verbal_interaction
        is_previous_turn_confirm_before_search = (
            previous_verbal_intent is not None
            and previous_verbal_intent.type == SimBotIntentType.confirm_before_search
        )

        return is_previous_turn_confirm_before_search

    def _agent_asked_for_confirm_before_plan(
        self, previous_turn: Optional[SimBotSessionTurn]
    ) -> bool:
        """Did the agent explicitly ask for confirmation before performing an action?"""
        return (
            previous_turn is not None
            and previous_turn.intent.verbal_interaction is not None
            and previous_turn.intent.verbal_interaction.type
            == SimBotIntentType.confirm_before_plan
        )
