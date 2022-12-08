from loguru import logger

from emma_experience_hub.api.clients import CompoundSplitterClient
from emma_experience_hub.datamodels.simbot import SimBotSession


class SimBotCompoundSplitterPipeline:
    """A component that splits complex instructions into smaller and simpler ones."""

    def __init__(self, compound_splitter_client: CompoundSplitterClient) -> None:
        self.compound_splitter_client = compound_splitter_client

    def run(self, session: SimBotSession) -> SimBotSession:
        """Given the user instruction, updates the utterance queue with simpler instructions."""
        if not session.current_turn.speech:
            logger.warning(
                "There is no utterance to extract intent from. Therefore the user has not explicitly told us to do anything. Why has this pipeline been called?"
            )
            return session

        user_utterance = session.current_turn.speech.utterance

        session.current_state.utterance_queue.extend_tail(
            self.compound_splitter_client.split(user_utterance)
        )

        return session
