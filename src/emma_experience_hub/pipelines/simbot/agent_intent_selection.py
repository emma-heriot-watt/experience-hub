from typing import NamedTuple, Optional

from loguru import logger

from emma_experience_hub.api.clients.simbot import (
    SimbotActionPredictionClient,
    SimBotFeaturesClient,
    SimBotNLUIntentClient,
)
from emma_experience_hub.datamodels import EnvironmentStateTurn
from emma_experience_hub.datamodels.simbot import (
    SimBotIntent,
    SimBotIntentType,
    SimBotNLUIntentType,
    SimBotPhysicalInteractionIntentType,
    SimBotSession,
    SimBotSessionTurn,
    SimBotUserIntentType,
    SimBotVerbalInteractionIntentType,
)
from emma_experience_hub.parsers import NeuralParser


class SimBotAgentIntents(NamedTuple):
    """Tuple of selected agent intents."""

    interaction: Optional[SimBotIntent[SimBotPhysicalInteractionIntentType]] = None
    language_condition: Optional[SimBotIntent[SimBotVerbalInteractionIntentType]] = None


class SimBotAgentIntentSelectionPipeline:
    """Determine HOW the agent should act given all the information.

    By only caring about how the agent should act, we separate intent extraction from the users
    expectations and how the agent chooses to act to those expectations.
    """

    def __init__(
        self,
        features_client: SimBotFeaturesClient,
        nlu_intent_client: SimBotNLUIntentClient,
        nlu_intent_parser: NeuralParser[SimBotIntent[SimBotNLUIntentType]],
        action_predictor_client: SimbotActionPredictionClient,
        _enable_clarification_questions: bool = True,
        _enable_search_actions: bool = True,
    ) -> None:
        self._features_client = features_client

        self._nlu_intent_client = nlu_intent_client
        self._nlu_intent_parser = nlu_intent_parser

        self._action_predictor_client = action_predictor_client

        self._enable_clarification_questions = _enable_clarification_questions
        self._enable_search_actions = _enable_search_actions

    def run(self, session: SimBotSession) -> SimBotAgentIntents:
        """Decide next action for the agent."""
        # If the user has said something, give that priority.
        if session.current_turn.intent.user:
            logger.debug("Getting agent intent from user intent.")

            # If we have received an invalid utterance, the agent does not act
            if SimBotIntentType.is_invalid_utterance_intent_type(session.current_turn.intent.user):
                return SimBotAgentIntents()

            # Otherwise, extract the intent from the user utterance
            if SimBotIntentType.is_user_intent_type(session.current_turn.intent.user):
                return self.extract_intent_from_user_utterance(
                    session.current_turn.intent.user, session
                )

        # If the environment has changed in a way that we did not want/expect, respond to it
        if session.current_turn.intent.environment:
            logger.debug("Returning None as environment errors do not cause the agent to act.")
            return SimBotAgentIntents()

        # If we are currently in the middle of a search routine, continue it.
        if session.is_find_object_in_progress:
            logger.debug("Setting agent intent to search since we are currently in progress")
            return SimBotAgentIntents(SimBotIntent(type=SimBotIntentType.search))

        return SimBotAgentIntents(interaction=SimBotIntent(type=SimBotIntentType.act_one_match))

    def extract_intent_from_user_utterance(  # noqa: WPS212
        self, user_intent: SimBotUserIntentType, session: SimBotSession
    ) -> SimBotAgentIntents:
        """Determine what the agent should do next from the user intent.

        The `UserIntentExtractorPipeline` will determine whether or not the user has said something
        that we cannot/should not act on. Therefore, we can use this function to determine the
        action given the other cases, and return if none of those cases fit.
        """
        # If the user wants us to act, then do that.
        if user_intent == SimBotIntentType.act:
            # Check if the utterance matches one of the known templates
            if self._does_utterance_match_known_template(session):
                return SimBotAgentIntents(
                    interaction=SimBotIntent(type=SimBotIntentType.act_one_match)
                )

            # Otherwise, use the NLU to detect it
            return self._process_utterance_with_nlu(session)

        # If we are receiving an answer to a clarification question, then just act on it
        if user_intent == SimBotIntentType.clarify_answer:
            return SimBotAgentIntents(
                interaction=SimBotIntent(type=SimBotIntentType.act_one_match)
            )

        # If we are within a find routine AND received a confirmation response from the user
        if session.is_find_object_in_progress and user_intent.is_confirmation_response:
            # Then let the search routine decide how to handle it.
            return SimBotAgentIntents(interaction=SimBotIntent(type=SimBotIntentType.search))

        # If the agent explicitly asked a confirmation question in the previous turn
        if self._agent_asked_for_confirm_before_acting(session.previous_valid_turn):
            # And the user approved
            if user_intent == SimBotIntentType.confirm_yes:
                return SimBotAgentIntents(
                    interaction=SimBotIntent(type=SimBotIntentType.act_previous)
                )

            # And the user didn't approve
            if user_intent == SimBotIntentType.confirm_no:
                return SimBotAgentIntents()

        # In all other cases, just return the intent as the agent _should_ know how to act.
        return SimBotAgentIntents(interaction=SimBotIntent(type=SimBotIntentType.act_one_match))

    def _process_utterance_with_nlu(self, session: SimBotSession) -> SimBotAgentIntents:
        """Perform NLU on the utterance to determine what the agent should do next.

        This is primarily used to determine whether the agent should act or ask for more
        information.
        """
        intent = self._nlu_intent_parser(
            self._nlu_intent_client.generate(
                dialogue_history=session.current_turn.utterances,
                environment_state_history=[
                    EnvironmentStateTurn(
                        features=self._features_client.get_features(session.current_turn)
                    )
                ],
            )
        )
        logger.debug(f"Extracted intent: {intent}")

        if not self._enable_clarification_questions and intent.type.is_clarification_question:
            logger.info(
                "Clarification questions are disabled; returning the `<act><one_match>` intent."
            )
            return SimBotAgentIntents(
                interaction=SimBotIntent(type=SimBotIntentType.act_one_match)
            )

        if not self._enable_search_actions and intent.type == SimBotIntentType.search:
            logger.info("Search actions are disabled; returning the `<act><one_match>` intent.")
            return SimBotAgentIntents(
                interaction=SimBotIntent(type=SimBotIntentType.act_one_match)
            )

        if SimBotIntentType.is_physical_interaction_intent_type(intent.type):
            return SimBotAgentIntents(
                interaction=SimBotIntent(
                    type=intent.type, action=intent.action, entity=intent.entity
                )
            )

        if SimBotIntentType.is_verbal_interaction_intent_type(intent.type):
            return SimBotAgentIntents(
                language_condition=SimBotIntent(
                    type=intent.type, action=intent.action, entity=intent.entity
                )
            )

        raise NotImplementedError(
            "All NLU intents are not accounted for. This means that NLU has returned an intent which does not map to either an interaction intent, or a response intent."
        )

    def _does_utterance_match_known_template(self, session: SimBotSession) -> bool:
        """Determine what the agent should do next from the user intent."""
        raw_text_match_prediction = (
            self._action_predictor_client.get_low_level_prediction_from_raw_text(
                dialogue_history=session.current_turn.utterances,
                environment_state_history=[],
            )
        )
        return raw_text_match_prediction is not None

    def _agent_asked_for_confirm_before_acting(
        self, previous_turn: Optional[SimBotSessionTurn]
    ) -> bool:
        """Did the agent explicitly ask for confirmation before performing an action?"""
        return (
            previous_turn is not None
            and previous_turn.intent.verbal_interaction is not None
            and previous_turn.intent.verbal_interaction.type.triggers_confirmation_question
        )
