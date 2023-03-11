from loguru import logger

from emma_experience_hub.api.clients import CompoundSplitterClient
from emma_experience_hub.datamodels.simbot import SimBotSession, SimBotUserSpeech


class SimBotCompoundSplitterPipeline:
    """A component that splits complex instructions into smaller and simpler ones."""

    def __init__(self, compound_splitter_client: CompoundSplitterClient) -> None:
        self.compound_splitter_client = compound_splitter_client

    def run(self, session: SimBotSession) -> SimBotSession:
        """Given the user instruction, updates the utterance queue with simpler instructions."""
        if not session.current_turn.speech:
            logger.warning(
                "There is no utterance to extract intent from. Therefore the user has not explicitly told us to do anything."
            )
            return session

        # Split the utterances
        utterance_splits = self.compound_splitter_client.split(
            session.current_turn.speech.utterance
        )

        # If there is less than 2 utterances after splitting, it means that the utterance cannot be split
        if len(utterance_splits) < 2:
            logger.debug("Utterance cannot be split into multiple parts.")
            return session

        logger.debug(f"Utterance split into {len(utterance_splits)} utterances.")

        self._add_utterances_to_queue(utterance_splits, session)
        self._replace_utterance_for_current_turn(session)
        return session

    def run_coreference_resolution(self, session: SimBotSession) -> SimBotSession:
        """Given the current and previous user instruction, perform coreference resolution."""
        previous_instruction = session.get_previous_user_intruction()
        if session.current_turn.speech is None or previous_instruction is None:
            logger.warning("There are no utterances to resolve coreferences.")
            return session
        new_utterance = self.compound_splitter_client.resolve_coreferences(
            instructions=[previous_instruction, session.current_turn.speech.utterance]
        )
        session.current_turn.speech = SimBotUserSpeech(utterance=new_utterance)
        return session

    def _add_utterances_to_queue(self, utterances: list[str], session: SimBotSession) -> None:
        """Add all the utterances to the queue."""
        logger.debug("Adding utterances to the queue")
        session.current_state.utterance_queue.extend_tail(utterances)

    def _replace_utterance_for_current_turn(self, session: SimBotSession) -> None:
        """Replace the utterance for the current turn with the one in the queue."""
        if not session.current_turn.speech:
            return

        new_utterance = session.current_state.utterance_queue.pop_from_head()

        logger.debug(
            f"Replacing current utterance ('{session.current_turn.speech.utterance}') with head of utterance queue ('{new_utterance}')"
        )

        session.current_turn.speech = SimBotUserSpeech(utterance=new_utterance)
