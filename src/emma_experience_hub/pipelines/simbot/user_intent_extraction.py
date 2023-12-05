from contextlib import suppress
from typing import Optional

from loguru import logger

from emma_experience_hub.datamodels.simbot import (
    SimBotIntentType,
    SimBotSession,
    SimBotSessionTurn,
    SimBotUserIntentType,
    SimBotVerbalInteractionIntentType,
)


class SimBotUserIntentExtractionPipeline:
    """Determine what the user wants us to do.

    This is explicitly about figuring out what the user WANTS us to do, not HOW we choose to go
    about it.
    """

    def __init__(
        self,
        _enable_clarification_questions: bool = True,
    ) -> None:
        self._enable_clarification_questions = _enable_clarification_questions

    def run(self, session: SimBotSession) -> Optional[SimBotUserIntentType]:
        """Run the pipeline to get the user's intent.

        We create assertions when processing questions responses, but if any of those occur, we
        default to let the model try to act on the utterance the best it can.
        """
        if not session.current_turn.speech:
            logger.warning(
                "There is no utterance to extract intent from. Therefore the user has not explicitly told us to do anything. Why has this pipeline been called?"
            )
            return None

        # Did the agent as the user a question in the previous turn?
        if self._was_question_asked_in_previous_turn(session.previous_valid_turn):
            # Previous turn DID have a question to the user.
            with suppress(AssertionError, NotImplementedError):
                return self.handle_response_to_question(session)

        # If nothing else, just let the model try to act.
        return SimBotIntentType.act

    def handle_response_to_question(self, session: SimBotSession) -> SimBotUserIntentType:
        """Handle responses to questions from the agent.

        This method refers to others that raise assertions and exceptions. These must be caught
        when calling this method.
        """
        verbal_interaction_intent_type = self._get_verbal_interaction_intent_from_turn(
            session.previous_valid_turn
        )

        # Did agent ask for disambiguation?
        if verbal_interaction_intent_type.triggers_disambiguation_question:
            return self.handle_clarification_response()

        raise NotImplementedError("There is no known way to handle the type of question provided.")

    def handle_clarification_response(self) -> SimBotUserIntentType:
        """Handle utterance that is responding to a clarification question.

        Note: Verify that the utterance _is_ responding to a question before calling this method.
        """
        # Assume it's a clarification answerr
        return SimBotIntentType.clarify_answer

    def _was_question_asked_in_previous_turn(
        self, previous_turn: Optional[SimBotSessionTurn]
    ) -> bool:
        """Was a question asked by the agent in the previous turn?"""
        if not self._enable_clarification_questions:
            return False
        if self._was_previous_action_unsuccessful(previous_turn):
            return False
        return self._was_question_intended_in_previous_turn(previous_turn)

    def _was_question_intended_in_previous_turn(
        self, previous_turn: Optional[SimBotSessionTurn]
    ) -> bool:
        """Was a question intended by the agent in the previous turn?"""
        return (
            previous_turn is not None
            and previous_turn.actions.dialog is not None
            and previous_turn.intent.verbal_interaction is not None
            and previous_turn.intent.verbal_interaction.type.triggers_question_to_user
        )

    def _was_previous_action_unsuccessful(
        self, previous_turn: Optional[SimBotSessionTurn]
    ) -> bool:
        """Was the previous action unsuccessful?"""
        if previous_turn is None:
            return False
        if previous_turn.actions.interaction is None:
            return False
        return not previous_turn.actions.interaction.is_successful

    def _get_verbal_interaction_intent_from_turn(
        self, turn: Optional[SimBotSessionTurn]
    ) -> SimBotVerbalInteractionIntentType:
        """Get the agent intent from the session turn, if it's available."""
        if turn is None:
            raise AssertionError()
        if turn.intent.verbal_interaction is None:
            raise AssertionError()
        return turn.intent.verbal_interaction.type
