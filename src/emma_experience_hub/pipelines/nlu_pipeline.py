from emma_experience_hub.api.clients import SimBotCacheClient
from emma_experience_hub.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.simbot import SimBotIntent, SimBotSession, SimBotSessionTurn
from emma_experience_hub.datamodels.simbot.intents import SimBotIntentType


class NLUPipeline:
    """Process the latest session turn and return the intent."""

    def __init__(
        self, extracted_features_cache_client: SimBotCacheClient[list[EmmaExtractedFeatures]]
    ) -> None:
        self._extracted_features_cache_client = extracted_features_cache_client

    def run(self, session: SimBotSession) -> SimBotSession:
        """Run the pipeline for the session."""
        # Check whether or not the utterance contains profanity
        if self._utterance_contains_profanity(session.current_turn):
            session.current_turn.intent = SimBotIntent(type=SimBotIntentType.profanity)
            return session

        # TODO: Extract intents from the utterance

        # TODO: Update the state of the turn

        # TODO: Return the session
        raise NotImplementedError()

    def extract_intent(self, turn: SimBotSessionTurn) -> SimBotIntent:
        """Extract the intent from the given turn."""
        raise NotImplementedError()

    def _utterance_contains_profanity(self, turn: SimBotSessionTurn) -> bool:
        """Detect whether the turn has profanity in it."""
        utterance = turn.speech.utterance

        # TODO: Add calls to check for profanity

        # TODO: Return if there is profanity
        return False
