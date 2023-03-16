from emma_common.datamodels import SpeakerRole
from emma_experience_hub.constants.simbot import get_arena_definitions
from emma_experience_hub.datamodels.simbot import (
    SimBotActionType,
    SimBotIntentType,
    SimBotSession,
    SimBotSessionTurn,
    SimBotUserSpeech,
)
from emma_experience_hub.datamodels.simbot.queue import SimBotQueueUtterance


class SimBotEnvironmentErrorCatchingPipeline:
    """Catch environment errors."""

    def __init__(self) -> None:
        self.error_handlers = {
            SimBotIntentType.already_holding_object: self._handle_already_holding_object_action_error,
            SimBotIntentType.receptacle_is_closed: self._handle_receptacle_is_closed_action_error,
            SimBotIntentType.target_out_of_range: self._handle_target_out_of_range_error,
            SimBotIntentType.unsupported_action: self._handle_unsupported_action_error,
        }

        self.unsupported_action_handlers = {
            SimBotActionType.Open: self._handle_open_action_execution_error,
        }
        arena_definitions = get_arena_definitions()
        self._openable_objects = [
            entity.lower() for entity in arena_definitions["openable_objects"]
        ]
        self._cleanable_objects = [
            entity.lower() for entity in arena_definitions["cleanable_objects"]
        ]
        self._fillable_objects = [
            entity.lower() for entity in arena_definitions["fillable_objects"]
        ]

    def __call__(self, session: SimBotSession) -> bool:
        """Process environment state changes to inform the agent of its standing in the world."""
        # Check that there was an environment erro
        environment_error = session.current_turn.intent.environment
        previous_turn = session.previous_valid_turn
        if environment_error is None or previous_turn is None:
            return False
        # Make sure we have the environment error entity
        environment_error_entity = environment_error.entity
        if environment_error_entity is None:
            return False

        error_handler = self.error_handlers.get(environment_error.type, None)
        if error_handler is None:
            return False
        # If the error was caught, set the user intent to act to continue acting
        caught_environmnent_error = error_handler(
            session, previous_turn=previous_turn, target=environment_error_entity.lower()
        )
        if caught_environmnent_error:
            session.current_turn.intent.user = SimBotIntentType.act
        return caught_environmnent_error

    def _handle_already_holding_object_action_error(
        self, session: SimBotSession, previous_turn: SimBotSessionTurn, target: str
    ) -> bool:
        """Handle already holding object action error."""
        # Check if we are holding the same type of object
        if target == session.current_state.inventory.entity.lower():
            # Continue executing the current utterance if the user intent was set.
            return session.current_turn.intent.user is not None
        return False

    def _handle_receptacle_is_closed_action_error(
        self, session: SimBotSession, previous_turn: SimBotSessionTurn, target: str
    ) -> bool:
        """Handle receptacle is closed."""
        # Continue executing the current utterance if the user intent was set.
        if session.current_turn.intent.user is None:
            return False
        return self._fix_and_repeat_failed_instruction(
            session=session,
            previous_turn=previous_turn,
            new_current_utterance=f"open the {target}",
        )

    def _handle_target_out_of_range_error(
        self, session: SimBotSession, previous_turn: SimBotSessionTurn, target: str
    ) -> bool:
        """Handle target out of range error.

        Go to the object and repeat the instruction.
        """
        return self._fix_and_repeat_failed_instruction(
            session=session,
            previous_turn=previous_turn,
            new_current_utterance=f"go to the {target}",
        )

    def _handle_unsupported_action_error(
        self, session: SimBotSession, previous_turn: SimBotSessionTurn, target: str
    ) -> bool:
        """Handle unsupported action error depending on the action type."""
        if previous_turn.actions.interaction is not None:
            previous_action = previous_turn.actions.interaction.type
            unsupported_action_handler = self.unsupported_action_handlers.get(
                previous_action, None
            )
            if unsupported_action_handler is None:
                return False
            return unsupported_action_handler(session, target)

        return False

    def _handle_open_action_execution_error(self, session: SimBotSession, target: str) -> bool:
        """Ignore an error from trying to open a target.

        Continue executing the current utterance if the user intent was set.
        """
        if target not in self._openable_objects:
            return False
        # If we have a new user utterance, continue handling that
        if session.current_turn.intent.user is not None:
            return True
        # If the action was not an end of trajectory, try executing the next action
        previous_action_was_end_of_trajectory = (
            session.previous_valid_turn is not None
            and session.previous_valid_turn.actions.interaction is not None
            and session.previous_valid_turn.actions.interaction.is_end_of_trajectory
        )
        return not previous_action_was_end_of_trajectory

    def _handle_fill_action_execution_error(self, session: SimBotSession, target: str) -> bool:
        """Retry to turn on the sink and fill the holding object."""
        if target != "sink" and target is self._fillable_objects:
            return False
        self._store_current_utterance_if_needed(session)
        queue_elem = SimBotQueueUtterance(utterance=f"fill the {target}", role=SpeakerRole.agent)
        session.current_state.utterance_queue.append_to_head(queue_elem)
        session.current_turn.speech = SimBotUserSpeech(
            utterance="toggle the sink", role=SpeakerRole.agent
        )
        return True

    def _handle_clean_action_execution_error(self, session: SimBotSession, target: str) -> bool:
        """Retry to turn on the sink and clean the holding object."""
        if target != "sink" and target is self._cleanable_objects:
            return False
        self._store_current_utterance_if_needed(session)
        queue_elem = SimBotQueueUtterance(utterance=f"clean the {target}", role=SpeakerRole.agent)
        session.current_state.utterance_queue.append_to_head(queue_elem)
        session.current_turn.speech = SimBotUserSpeech(
            utterance="toggle the sink", role=SpeakerRole.agent
        )
        return True

    def _store_current_utterance_if_needed(self, session: SimBotSession) -> None:
        """If there is a new instruction in this turn, store it for later."""
        if session.current_turn.intent.user != SimBotIntentType.act:
            return

        if session.current_turn.speech is not None:
            queue_elem = SimBotQueueUtterance(
                utterance=session.current_turn.speech.utterance, role=SpeakerRole.agent
            )
        session.current_state.utterance_queue.append_to_head(queue_elem)

    def _fix_and_repeat_failed_instruction(
        self, session: SimBotSession, previous_turn: SimBotSessionTurn, new_current_utterance: str
    ) -> bool:
        """Fix the state causing the error and repeat the failed instruction."""
        previous_speech = previous_turn.speech
        if previous_speech is None:
            return False
        # Add the current instruction to the utterrance queue
        self._store_current_utterance_if_needed(session)
        # Add the failed instruction to the utterance queue
        queue_elem = SimBotQueueUtterance(
            utterance=previous_speech.utterance, role=previous_speech.role
        )
        session.current_state.utterance_queue.append_to_head(queue_elem)
        # Add a new instruction to fix the state
        session.current_turn.speech = SimBotUserSpeech(
            utterance=new_current_utterance, role=previous_speech.role
        )
        return True
