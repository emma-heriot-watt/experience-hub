from typing import Optional

from loguru import logger

from emma_experience_hub.api.clients import ConfirmationResponseClassifierClient
from emma_experience_hub.datamodels.simbot import (
    SimBotIntentType,
    SimBotSession,
    SimBotSessionTurn,
)


class SimBotUserIntentExtractionPipeline:
    """Determine what the user wants us to do.

    This is explicitly about figuring out what the user WANTS us to do, not HOW we choose to go
    about it.
    """

    def __init__(
        self,
        confirmation_response_classifier: ConfirmationResponseClassifierClient,
        _disable_clarification_questions: bool = False,
        _disable_clarification_confirmation: bool = False,
    ) -> None:
        self._confirmation_response_classifier = confirmation_response_classifier

        # Feature flags
        self._disable_clarification_questions = _disable_clarification_questions
        self._disable_clarification_confirmation = _disable_clarification_confirmation

    def run(self, session: SimBotSession) -> Optional[SimBotIntentType]:
        """Run the pipeline to get the user's intent."""
        if not session.current_turn.speech:
            logger.warning(
                "There is no utterance to extract intent from. Therefore the user has not explicitly told us to do anything. Why has this pipeline been called?"
            )
            return None

        # Check if the question was a confirmation request
        if self._utterance_responding_to_confirm_request(session.previous_valid_turn):
            logger.debug("Utterance is responding to a confirmation request.")
            return self.handle_confirmation_request_approval(session.current_turn)

        # Check if we are dealing with a clarification response
        if self._utterance_is_responding_to_clarify_question(session.previous_valid_turn):
            logger.debug("Utterance is a response to a clarification question.")
            return self.handle_clarification_response(session)

        # If nothing else, just let the model try to act.
        return SimBotIntentType.act

    def handle_clarification_response(self, session: SimBotSession) -> SimBotIntentType:
        """Handle utterance that is responding to a clarification question.

        Note: Verify that the utterance _is_ responding to a question before calling this method.
        """
        # Assume it's a clarification answerr
        return SimBotIntentType.clarify_answer

    def handle_confirmation_request_approval(
        self, current_turn: SimBotSessionTurn
    ) -> SimBotIntentType:
        """Check if the confirmation request was approved and return the correct intent."""
        if not current_turn.speech:
            raise AssertionError("There should be an utterance to verify.")

        # Tell agent to use generated action from previous turn if true
        if self._is_confirmation_request_approved(current_turn.speech.utterance):
            logger.debug("Utterance approves of confirmation request.")
            return SimBotIntentType.act_previous

        logger.debug("Utterance denies confirmation request.")
        return SimBotIntentType.generic_failure

    def _utterance_is_responding_to_clarify_question(
        self, previous_turn: Optional[SimBotSessionTurn]
    ) -> bool:
        """Return True if the user is responding to a previous clarification question."""
        return (
            previous_turn is not None
            and previous_turn.actions.dialog is not None
            and previous_turn.actions.dialog.intent.is_clarification_question
            # This will always resolve False if clarification questions are disabled
            and not self._disable_clarification_questions
        )

    def _utterance_responding_to_confirm_request(
        self, previous_turn: Optional[SimBotSessionTurn]
    ) -> bool:
        """Return True if the user is responding to a confirmation question."""
        return (
            previous_turn is not None
            and previous_turn.actions.dialog is not None
            and previous_turn.actions.dialog.intent.is_clarification_question
            # This will always resolve to False if clarification questions are disabled.
            and not self._disable_clarification_confirmation
        )

    def _is_confirmation_request_approved(self, utterance: str) -> bool:
        """Return True if the confirmation request was approved from the user."""
        return self._confirmation_response_classifier.is_confirmation(utterance)
