from emma_experience_hub.api.clients import EmmaPolicyClient, ProfanityFilterClient
from emma_experience_hub.api.clients.simbot import SimBotCacheClient
from emma_experience_hub.common.logging import get_logger
from emma_experience_hub.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.simbot import (
    SimBotIntent,
    SimBotIntentType,
    SimBotSession,
    SimBotSessionTurn,
)
from emma_experience_hub.parsers import NeuralParser


logger = get_logger()


class SimBotNLUPipeline:
    """Process the latest session turn and return the intent."""

    def __init__(
        self,
        extracted_features_cache_client: SimBotCacheClient[list[EmmaExtractedFeatures]],
        profanity_filter_client: ProfanityFilterClient,
        nlu_intent_client: EmmaPolicyClient,
        nlu_intent_parser: NeuralParser[SimBotIntent],
    ) -> None:
        self._extracted_features_cache_client = extracted_features_cache_client
        self._profanity_filter_client = profanity_filter_client

        self._nlu_intent_client = nlu_intent_client
        self._nlu_intent_parser = nlu_intent_parser

    def run(self, session: SimBotSession) -> SimBotSession:
        """Run the pipeline for the session."""
        # Bypass the NLU pipeline if there is no utterance to extract intent from
        if not session.current_turn.speech:
            logger.debug("There is no utterance to extract intent from.")
            return session

        # Check whether or not the utterance contains profanity
        if self._utterance_contains_profanity(session.current_turn):
            logger.debug("Utterance contains profanity.")
            session.current_turn.intent = SimBotIntent(type=SimBotIntentType.profanity)
            return session

        # Extract the intent, store within the session, and return
        session.current_turn.intent = self.extract_intent(session)
        return session

    def extract_intent(self, session: SimBotSession) -> SimBotIntent:
        """Extract the intent from the given turn."""
        raw_intent = self._nlu_intent_client.generate(
            dialogue_history=session.get_dialogue_history(
                session.get_turns_from_most_recent_instruction()
            ),
            environment_state_history=session.get_environment_state_history(
                session.get_turns_from_most_recent_instruction(),
                self._extracted_features_cache_client.load,
            ),
        )
        intent = self._nlu_intent_parser(raw_intent)
        logger.info(f"Extracted intent from turn: {intent}")
        return SimBotIntent(type=SimBotIntentType.instruction)

    def _utterance_contains_profanity(self, turn: SimBotSessionTurn) -> bool:
        """Detect whether the turn has profanity in it."""
        # Return False if there is no utterance
        if turn.speech is None:
            return False

        try:
            return self._profanity_filter_client.is_profane(turn.speech.utterance)
        except Exception as err:
            # TODO: What to do if we cannot determine?
            logger.exception("Unable to check for profanity.", exc_info=err)
            raise err
