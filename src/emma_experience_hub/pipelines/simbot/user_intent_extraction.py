from contextlib import suppress
from typing import Optional

from loguru import logger
from opentelemetry import trace

from emma_experience_hub.api.clients import ConfirmationResponseClassifierClient
from emma_experience_hub.api.clients.simbot import SimBotQAIntentClient
from emma_experience_hub.datamodels.simbot import (
    SimBotIntentType,
    SimBotSession,
    SimBotSessionTurn,
    SimBotUserIntentType,
    SimBotVerbalInteractionIntentType,
)
from emma_experience_hub.datamodels.simbot.enums.intents import SimBotUserQAType
from emma_experience_hub.parsers.simbot import SimBotQAOutputParser


tracer = trace.get_tracer(__name__)


class SimBotUserIntentExtractionPipeline:
    """Determine what the user wants us to do.

    This is explicitly about figuring out what the user WANTS us to do, not HOW we choose to go
    about it.
    """

    def __init__(
        self,
        confirmation_response_classifier: ConfirmationResponseClassifierClient,
        qa_intent_client: SimBotQAIntentClient,
        qa_intent_parser: SimBotQAOutputParser,
        _enable_object_related_questions: bool = False,
        _enable_simbot_qa: bool = True,
    ) -> None:
        self._confirmation_response_classifier = confirmation_response_classifier

        self._qa_intent_client = qa_intent_client
        self._qa_intent_parser = qa_intent_parser

        self._enable_object_related_questions = _enable_object_related_questions
        self._enable_simbot_qa = _enable_simbot_qa

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

        # Check if the user is asking about QA or similar?
        if self._enable_simbot_qa:
            with suppress(AssertionError):
                return self.check_for_user_qa(session.current_turn.speech.utterance)

        # Did the agent as the user a question in the previous turn?
        if self._was_question_asked_in_previous_turn(session.previous_valid_turn):
            # Previous turn DID have a question to the user.
            with suppress(AssertionError, NotImplementedError):
                return self.handle_response_to_question(session)

        # If nothing else, just let the model try to act.
        return SimBotIntentType.act

    @tracer.start_as_current_span("Check for user QA")
    def check_for_user_qa(self, utterance: str) -> Optional[SimBotUserQAType]:
        """Check if the user is asking us a question or are unparsable utterances."""
        raw_user_qa_intent = self._qa_intent_client.process_utterance(utterance)
        if not raw_user_qa_intent:
            raise AssertionError("No user QA intent")

        user_qa_intent = self._qa_intent_parser(raw_user_qa_intent)
        if not user_qa_intent:
            raise AssertionError("No user QA intent")

        # Ignore QAs about specific objects
        if user_qa_intent.is_user_qa_about_object and not self._enable_object_related_questions:
            logger.debug("Replacing user QA intent with ask_about_game.")
            user_qa_intent = SimBotIntentType.ask_about_game

        logger.debug(f"User QA Intent: {user_qa_intent}")
        return user_qa_intent

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

        # Did agent ask for confirmation?
        if verbal_interaction_intent_type.triggers_confirmation_question:
            return self.handle_confirmation_request_approval(session)

        raise NotImplementedError("There is no known way to handle the type of question provided.")

    def handle_clarification_response(self) -> SimBotUserIntentType:
        """Handle utterance that is responding to a clarification question.

        Note: Verify that the utterance _is_ responding to a question before calling this method.
        """
        # Assume it's a clarification answerr
        return SimBotIntentType.clarify_answer

    def handle_confirmation_request_approval(self, session: SimBotSession) -> SimBotUserIntentType:
        """Check if the confirmation request was approved and return the correct intent."""
        # Make sure the user utterance exists
        if not session.current_turn.speech:
            raise AssertionError("There is no utterance from the user? That's not right")
        utterance = session.current_turn.speech.utterance.lower()

        # Make sure the agent question exists
        if session.previous_turn is None or session.previous_turn.actions.dialog is None:
            raise AssertionError("There is no question from the agent? That's not right")
        previous_dialog_action = session.previous_turn.actions.dialog
        previous_agent_utterance = previous_dialog_action.payload.value.lower()

        # Run the confirmation classifier
        confirmation_approved = self._confirmation_response_classifier.is_request_approved(
            " ".join([previous_agent_utterance, utterance]).lower()
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
            return True
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
