from loguru import logger

from emma_common.datamodels import SpeakerRole
from emma_experience_hub.api.clients import CompoundSplitterClient
from emma_experience_hub.datamodels.simbot import SimBotSession, SimBotUserSpeech
from emma_experience_hub.datamodels.simbot.queue import SimBotQueueUtterance


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

    def run_high_level_planner(self, session: SimBotSession) -> SimBotSession:
        """Given the user instruction, updates the utterance queue with simpler instructions."""
        skip_high_level_conditions = [
            not session.current_turn.speech
            or session.current_turn.speech.role == SpeakerRole.agent
        ]

        if any(skip_high_level_conditions):
            logger.warning("There is no utterance to split into simple instructions.")
            return session

        # Split the utterances
        utterance_splits = self.compound_splitter_client.high_level_plan(
            session.current_turn.speech.utterance, session.current_state.inventory.entity
        )

        # If there is less than 2 utterances after splitting, it means that the utterance cannot be split
        if len(utterance_splits) < 2:
            logger.debug("Utterance was already a simple instruction.")
            return session

        logger.debug(f"High-level split into {len(utterance_splits)} simple instructions.")

        self._add_utterances_to_queue(utterance_splits, session)
        self._replace_utterance_for_current_turn(session)
        return session

    def run_coreference_resolution(self, session: SimBotSession) -> SimBotSession:
        """Given the current and previous user instruction, perform coreference resolution."""
        if len(session.current_state.last_user_utterance) <= 1:
            logger.warning("There are no utterances to resolve coreferences.")
            return session
        previous_instruction = session.current_state.last_user_utterance.queue[1]
        new_utterance = self.compound_splitter_client.resolve_coreferences(
            instructions=[previous_instruction, session.current_turn.speech.utterance]
        )
        session.current_turn.speech = SimBotUserSpeech(
            utterance=new_utterance,
            original_utterance=session.current_turn.speech.original_utterance
            if session.current_turn.speech is not None
            else None,
        )
        return session

    def _add_utterances_to_queue(self, utterances: list[str], session: SimBotSession) -> None:
        """Add all the utterances to the queue."""
        logger.debug("Adding utterances to the queue")
        session.current_state.utterance_queue.extend_tail(
            SimBotQueueUtterance(utterance=utterance, role=SpeakerRole.agent)
            for utterance in utterances
        )

    def _replace_utterance_for_current_turn(self, session: SimBotSession) -> None:
        """Replace the utterance for the current turn with the one in the queue."""
        if not session.current_turn.speech:
            return

        queue_elem = session.current_state.utterance_queue.pop_from_head()
        new_utterance = queue_elem.utterance

        logger.debug(
            f"Replacing current utterance ('{session.current_turn.speech.utterance}') with head of utterance queue ('{new_utterance}')"
        )

        session.current_turn.speech = SimBotUserSpeech(
            utterance=new_utterance,
            from_utterance_queue=True,
            role=queue_elem.role,
            original_utterance=session.current_turn.speech.original_utterance,
        )
