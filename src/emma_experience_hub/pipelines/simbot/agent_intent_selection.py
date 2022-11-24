from loguru import logger

from emma_experience_hub.api.clients import EmmaPolicyClient
from emma_experience_hub.api.clients.simbot import SimBotFeaturesClient
from emma_experience_hub.datamodels import EnvironmentStateTurn
from emma_experience_hub.datamodels.simbot import SimBotIntent, SimBotIntentType, SimBotSession
from emma_experience_hub.parsers import NeuralParser


class SimBotAgentIntentSelectionPipeline:
    """Determine HOW the agent should act given all the information.

    By only caring about how the agent should act, we separate intent extraction from the users
    expectations and how the agent chooses to act to those expectations.
    """

    def __init__(
        self,
        features_client: SimBotFeaturesClient,
        nlu_intent_client: EmmaPolicyClient,
        nlu_intent_parser: NeuralParser[SimBotIntent],
        _disable_clarification_questions: bool = False,
    ) -> None:
        self._features_client = features_client

        self._nlu_intent_client = nlu_intent_client
        self._nlu_intent_parser = nlu_intent_parser

        self._disable_clarification_questions = _disable_clarification_questions

    def run(self, session: SimBotSession) -> SimBotIntent:
        """Decide that the agent should do next."""
        # If the user has said something, give that priority.
        if session.current_turn.intent.user:
            logger.debug("Setting user intent as agent intent.")
            return self.extract_intent_from_user_utterance(
                session.current_turn.intent.user, session
            )

        # If the environment has changed in a way that we did not want/expect, respond to it
        if session.current_turn.intent.environment:
            logger.debug("Setting environment intent as the agent intent.")
            return session.current_turn.intent.environment

        # Otherwise, let the agent act
        return SimBotIntent(type=SimBotIntentType.act_low_level)

    def extract_intent_from_user_utterance(
        self, user_intent: SimBotIntentType, session: SimBotSession
    ) -> SimBotIntent:
        """Determine what the agent should do next from the user intent.

        The `UserIntentExtractorPipeline` will determine whether or not the user has said something
        that we cannot/should not act on. Therefore, we can use this function to determine the
        action given the other cases, and return if none of those cases fit.
        """
        # If the user wants us to act, then do that.
        if user_intent == SimBotIntentType.act:
            return self._process_utterance_with_nlu(session)

        # If the user has replied to a clarification question, then act
        if user_intent == SimBotIntentType.clarify_answer:
            # TODO: We can change this logic here to determine whether or not we should ask more
            #       questions or just act, if we want to start handling multi-turn dialogue
            return SimBotIntent(type=SimBotIntentType.act_low_level)

        # In all other cases, just return the intent as the agent _should_ know how to act.
        return SimBotIntent(type=user_intent)

    def _process_utterance_with_nlu(self, session: SimBotSession) -> SimBotIntent:
        """Perform NLU on the utterance to determine what the agent should do next.

        This is primarily used to determine whether the agent should act or ask for more
        information.
        """
        if self._disable_clarification_questions:
            logger.info(
                "Clarification questions are disabled; returning the `<act><low_level>` intent."
            )
            return SimBotIntent(type=SimBotIntentType.act_low_level)

        raw_intent = self._nlu_intent_client.generate(
            dialogue_history=session.current_turn.utterances,
            environment_state_history=[
                EnvironmentStateTurn(
                    features=self._features_client.get_features(session.current_turn)
                )
            ],
        )

        intent = self._nlu_intent_parser(raw_intent)
        logger.debug(f"Extracted intent from turn: {intent}")

        return intent
