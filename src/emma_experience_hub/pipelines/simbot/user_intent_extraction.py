from contextlib import suppress
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
        self, confirmation_response_classifier: ConfirmationResponseClassifierClient
    ) -> None:
        self._confirmation_response_classifier = confirmation_response_classifier

    def run(self, session: SimBotSession) -> Optional[SimBotIntentType]:
        """Run the pipeline to get the user's intent.

        We create assertions when processing questions responses, but if any of those occur, we
        default to let the model try to act on the utterance the best it can.
        """
        if not session.current_turn.speech:
            logger.warning(
                "There is no utterance to extract intent from. Therefore the user has not explicitly told us to do anything. Why has this pipeline been called?"
            )
            return None

        # Did the agent as the user aquestion in the previous turn?
        if self._was_question_asked_in_previous_turn(session.previous_valid_turn):
            # Previous turn DID have a question to the user.
            with suppress(AssertionError, NotImplementedError):
                return self.handle_response_to_question(session)

        # If nothing else, just let the model try to act.
        return SimBotIntentType.act

    def handle_response_to_question(self, session: SimBotSession) -> SimBotIntentType:
        """Handle responses to questions from the agent.

        This method refers to others that raise assertions and exceptions. These must be caught
        when calling this method.
        """
        agent_intent_type = self._get_agent_intent_from_turn(session.previous_valid_turn)

        # Did agent ask for disambiguation?
        if agent_intent_type.triggers_disambiguation_question:
            return self.handle_clarification_response()

        # Did agent ask for confirmation?
        if agent_intent_type.triggers_confirmation_question:
            # Make sure the user utterance exists
            if not session.current_turn.speech:
                raise AssertionError("There is no utterance from the user? That's not right")

            return self.handle_confirmation_request_approval(session.current_turn.speech.utterance)

        raise NotImplementedError("There is no known way to handle the type of question provided.")

    def handle_clarification_response(self) -> SimBotIntentType:
        """Handle utterance that is responding to a clarification question.

        Note: Verify that the utterance _is_ responding to a question before calling this method.
        """
        # Assume it's a clarification answerr
        return SimBotIntentType.clarify_answer

    def handle_confirmation_request_approval(self, utterance: str) -> SimBotIntentType:
        """Check if the confirmation request was approved and return the correct intent."""
        confirmation_approved = self._confirmation_response_classifier.is_request_approved(
            utterance
        )
        # If the utterance is NOT a response to the confirmation request
        if confirmation_approved is None:
            raise AssertionError("Utterance is not a response to the confirmation request")

        if confirmation_approved:
            logger.debug("Utterance approves of confirmation request.")
            return SimBotIntentType.confirm_yes

        logger.debug("Utterance denies confirmation request.")
        return SimBotIntentType.confirm_no

    def _was_question_asked_in_previous_turn(
        self, previous_turn: Optional[SimBotSessionTurn]
    ) -> bool:
        """Was a question asked by the agent in the previous turn?"""
        return (
            previous_turn is not None
            and previous_turn.actions.dialog is not None
            and previous_turn.intent.agent is not None
            and previous_turn.intent.agent.type.triggers_question_to_user
        )

    def _get_agent_intent_from_turn(self, turn: Optional[SimBotSessionTurn]) -> SimBotIntentType:
        """Get the agent intent from the session turn, if it's available."""
        if turn is None:
            raise AssertionError()
        if turn.intent.agent is None:
            raise AssertionError()
        return turn.intent.agent.type
