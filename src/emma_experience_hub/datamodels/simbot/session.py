import itertools
from collections.abc import Iterator
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import datetime
from functools import cached_property
from typing import Callable, Optional, cast

from loguru import logger
from overrides import overrides
from pydantic import BaseModel, Field, root_validator, validator

from emma_experience_hub.datamodels import (
    DialogueUtterance,
    EmmaExtractedFeatures,
    EnvironmentStateTurn,
)
from emma_experience_hub.datamodels.common import Position, RotationQuaternion
from emma_experience_hub.datamodels.simbot.actions import SimBotAction, SimBotActionType
from emma_experience_hub.datamodels.simbot.intents import SimBotIntent, SimBotIntentType
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotAuxiliaryMetadataUri,
    SimBotDialogPayload,
    SimBotObjectOutputType,
)
from emma_experience_hub.datamodels.simbot.queue import SimBotQueue
from emma_experience_hub.datamodels.simbot.request import SimBotRequest
from emma_experience_hub.datamodels.simbot.response import SimBotResponse
from emma_experience_hub.datamodels.simbot.speech import SimBotUserSpeech
from emma_experience_hub.functions.coordinates import get_closest_position_index_to_reference


class SimBotSessionTurnTimestamp(BaseModel):
    """Track the start and end time of each turn."""

    start: datetime = datetime.now()
    end: Optional[datetime] = None

    @property
    def processing_time(self) -> Optional[float]:
        """Calculate the timedelta in seconds, if it exists."""
        if self.end is None:
            return None

        delta = self.end - self.start
        return delta.total_seconds()


class SimBotSessionTurnIntent(BaseModel):
    """Intents from each actor within the environment for the turn.."""

    user: Optional[SimBotIntentType] = None
    environment: Optional[SimBotIntent] = None
    agent: Optional[SimBotIntent] = None

    @property
    def should_generate_interaction_action(self) -> bool:
        """Return True is the agent should generate an interaction action."""
        return self.agent is not None and self.agent.type.is_actionable


class SimBotSessionTurnActions(BaseModel, validate_assignment=True):
    """Actions generated by the agent.

    This class constrains us to never return more than one interaction action or dialog action for
    a given turn.

    The validators are called when the attributes are assigned to, making sure that the actions
    always have the correct IDs.
    """

    interaction: Optional[SimBotAction] = None
    dialog: Optional[SimBotAction] = None

    @overrides(check_signature=False)
    def __iter__(self) -> Iterator[SimBotAction]:
        """Return an iterator of actions.."""
        return iter(self.to_list())

    def __len__(self) -> int:
        """Get the number of actions in the arena."""
        return len(self.to_list())

    @root_validator
    @classmethod
    def update_action_ids(
        cls, values: dict[str, Optional[SimBotAction]]  # noqa: WPS110
    ) -> dict[str, Optional[SimBotAction]]:
        """Update the action IDs for the returned actions.

        Interaction actions are always first.
        """
        interaction_action = values.get("interaction")
        dialog_action = values.get("dialog")

        # Always set the interaction action ID to 0
        if interaction_action:
            interaction_action.id = 0

        # Set the dialog action to 1 if the is already an interaction action, else set it to 0
        if dialog_action:
            dialog_action.id = 1 if interaction_action is not None else 0

        return values

    @property
    def object_output_type(self) -> SimBotObjectOutputType:
        """Get the object output type used by the actions.

        If there are more than one type in the list, we have a problem.
        """
        if not self.to_list():
            return SimBotObjectOutputType.default()

        output_types = {
            action.object_output_type
            for action in self.to_list()
            if action.object_output_type is not None
        }

        if not output_types:
            return SimBotObjectOutputType.default()

        is_examine_sticky_note = (
            len(output_types) > 1
            and self.interaction is not None
            and self.interaction.type == SimBotActionType.Examine
        )

        if is_examine_sticky_note:
            return SimBotObjectOutputType.object_class

        if len(output_types) > 1:
            raise AssertionError(
                "There is more than one output type in this list. That will breka the response. We should not be returning more than one object-related interaction action per turn."
            )

        return next(iter(output_types))

    @property
    def is_successful(self) -> bool:
        """Return True is the interaction action was successful."""
        return self.interaction is not None and self.interaction.is_successful

    def to_list(self) -> list[SimBotAction]:
        """Return actions as a list.

        This returns an empty list if there are no actions.
        """
        actions_list: list[SimBotAction] = []

        if self.interaction:
            actions_list.append(self.interaction)

        if self.dialog:
            actions_list.append(self.dialog)

        return actions_list


class SimBotSessionTurnEnvironment(BaseModel):
    """Get environment information for the robot and any relevant locations."""

    current_room: str
    current_position: Position
    current_rotation: RotationQuaternion

    unique_room_names: set[str]
    viewpoints: dict[str, Position]

    @property
    def viewpoints_in_current_room(self) -> dict[str, Position]:
        """Only return the viewpoints within the same room the agent is in."""
        return {
            viewpoint_name: viewpoint_location
            for viewpoint_name, viewpoint_location in self.viewpoints.items()
            if viewpoint_name.startswith(self.current_room)
        }

    def get_closest_viewpoint_name(self) -> str:
        """Get the name of the closest viewpoint to the agent.

        Adapted from: https://codereview.stackexchange.com/a/28210
        """
        viewpoint_index = get_closest_position_index_to_reference(
            self.current_position, self.viewpoints_in_current_room.values()
        )
        # Use the index to get the name of the viewpoint
        viewpoint_name = list(self.viewpoints_in_current_room.keys())[viewpoint_index]
        return viewpoint_name


class SimBotSessionTurnState(BaseModel, validate_assignment=True):
    """Track the state of the session within the turn.

    The queue is a list of utterances which the model can use to predict successive actions from.
    """

    utterance_queue: SimBotQueue[str] = SimBotQueue[str]()
    find_queue: SimBotQueue[SimBotAction] = SimBotQueue[SimBotAction]()


class SimBotSessionTurn(BaseModel):
    """Current turn for a SimBot game session."""

    session_id: str
    prediction_request_id: str
    idx: int = Field(..., ge=0)

    timestamp: SimBotSessionTurnTimestamp

    speech: Optional[SimBotUserSpeech] = None

    # URI to the auxiliary metadata file, as provided by the SimBot Arena
    auxiliary_metadata_uri: SimBotAuxiliaryMetadataUri

    environment: SimBotSessionTurnEnvironment
    intent: SimBotSessionTurnIntent
    actions: SimBotSessionTurnActions
    state: SimBotSessionTurnState

    @classmethod
    def new_from_simbot_request(cls, request: SimBotRequest, idx: int) -> "SimBotSessionTurn":
        """Create a session turn from a SimBotRequest."""
        speech = (
            SimBotUserSpeech.from_speech_recognition_payload(request.speech_recognition)
            if request.speech_recognition
            else None
        )
        return cls(
            session_id=request.header.session_id,
            prediction_request_id=request.header.prediction_request_id,
            idx=idx,
            timestamp=SimBotSessionTurnTimestamp(),
            speech=speech,
            auxiliary_metadata_uri=request.auxiliary_metadata.uri,
            environment=SimBotSessionTurnEnvironment(
                unique_room_names=request.auxiliary_metadata.unique_room_names,
                viewpoints=request.auxiliary_metadata.viewpoints,
                current_room=request.auxiliary_metadata.current_room,
                current_position=request.auxiliary_metadata.current_position,
                current_rotation=request.auxiliary_metadata.current_rotation,
            ),
            intent=SimBotSessionTurnIntent(),
            actions=SimBotSessionTurnActions(),
            state=SimBotSessionTurnState(),
        )

    @property
    def utterances(self) -> list[DialogueUtterance]:
        """Get the utterances from the session turn, if any."""
        utterances: list[DialogueUtterance] = []

        # If there is a user utterance, add it first.
        if self.speech is not None:
            utterances.append(DialogueUtterance(utterance=self.speech.utterance, role="user"))

        # Do not include lightweight dialog actions within the utterances!
        if self.actions.dialog is not None and self.actions.dialog.type == SimBotActionType.Dialog:
            payload = cast(SimBotDialogPayload, self.actions.dialog.payload)
            utterances.append(DialogueUtterance(utterance=payload.value, role="agent"))

        return utterances

    def convert_to_simbot_response(self) -> SimBotResponse:
        """Convert the session turn to a SimBotResponse, to be returned to the API."""
        if not self.actions.to_list():
            raise AssertionError(
                "There is no action to be returned. Have you run the response generator on this?"
            )

        return SimBotResponse(
            sessionId=self.session_id,
            predictionRequestId=self.prediction_request_id,
            objectOutputType=self.actions.object_output_type,
            actions=self.actions.to_list(),
        )


class SimBotSession(BaseModel):
    """A single SimBot Game Session."""

    session_id: str

    turns: list[SimBotSessionTurn]

    class Config:
        """Config for the model.

        We need to explictly tell Pydantic to not touch the cached property.
        """

        keep_untouched = (cached_property,)

    @validator("turns")
    @classmethod
    def sort_session_turns(cls, turns: list[SimBotSessionTurn]) -> list[SimBotSessionTurn]:
        """Sort the session turns from oldest to newest."""
        # Sort from the oldest request to the newest request
        turns = sorted(turns, key=lambda turn: turn.timestamp.start)

        # Verify that indexes are in order
        if sorted(turns, key=lambda turn: turn.idx) != turns:
            # TODO: Is this the best way to handle this?
            raise AssertionError(
                "Ordering turns in date order is not the same as ordering in index order. Something is wrong here."
            )

        return turns

    @property
    def current_turn(self) -> SimBotSessionTurn:
        """Get the current turn being handled."""
        return self.turns[-1]

    @property
    def previous_turn(self) -> Optional[SimBotSessionTurn]:
        """Get the previous turn, if it exists."""
        try:
            return self.turns[-2]
        except IndexError:
            return None

    @cached_property
    def valid_turns(self) -> list[SimBotSessionTurn]:
        """Get all the valid turns from the list of turns.

        The current turn does not need to be valid, but all previous ones MUST be.

        If a given turn has a user intent AND that intent is valid, ignore it.
        If it doesn't have a user intent, or the user intent is valid, then let it through the filter.
        """
        valid_turns = [
            turn
            for turn in self.turns[:-1]
            if not (turn.intent.user and turn.intent.user.is_invalid_user_utterance)
        ]
        valid_turns.append(self.current_turn)
        return valid_turns

    @cached_property
    def previous_valid_turn(self) -> Optional[SimBotSessionTurn]:
        """Get the previous valid turn, if it exists."""
        try:
            return self.valid_turns[-2]
        except IndexError:
            return None

    @property
    def current_state(self) -> SimBotSessionTurnState:
        """Return the state from the most current turn."""
        return self.current_turn.state

    @property
    def is_find_object_in_progress(self) -> bool:
        """Is the find object pipeline currently in progress?"""
        return self.current_state.find_queue.is_not_empty

    @property
    def is_find_object_recently_finished(self) -> bool:
        """Was the find object pipeline recently finished?

        By recently, we are meaning that the last valid turn resulted in the clearing of the queue.
        """
        conditions = [
            # The find queue in the previous valid turn is empty (since it got reset when we found
            # the object, or when there are no actions left to take)
            self.previous_valid_turn is not None
            and self.previous_valid_turn.state.find_queue.is_empty,
            # The find queue in the valid turn BEFORE the previous valid turn IS NOT empty (since
            # there is at least one action left to take)
            len(self.valid_turns) > 2 and self.valid_turns[-3].state.find_queue.is_not_empty,
        ]
        return all(conditions)

    @property
    def is_finding_object(self) -> bool:
        """Return True if the agent is working on finding an object."""
        return self.is_find_object_in_progress or self.is_find_object_recently_finished

    def get_turns_within_interaction_window(self) -> list[SimBotSessionTurn]:
        """Get all the turns within the local interaction window.

        This gets all the turns since the last time the user initiated a new interaction.
        """
        turns_within_window = []

        # Iterate in reverse-order because we only care about the most recents turns
        for turn in self.valid_turns[::-1]:
            # Add the turn to the window
            turns_within_window.append(turn)

            # If the turn is the start of the local window, break
            if turn.intent.user and turn.intent.user == SimBotIntentType.act:
                break

        # Reverse the order within the list so that they are in the correct order
        turns_within_window.reverse()

        return turns_within_window

    @staticmethod
    def get_dialogue_history_from_session_turns(  # noqa: WPS602
        turns: list[SimBotSessionTurn],
    ) -> list[DialogueUtterance]:
        """Get a dialogue history from the given turns."""
        utterances_lists = (turn.utterances for turn in turns)
        dialogue_history = list(itertools.chain.from_iterable(utterances_lists))
        return dialogue_history

    @staticmethod
    def get_environment_state_history_from_turns(  # noqa: WPS602
        turns: list[SimBotSessionTurn],
        extracted_features_load_fn: Callable[[SimBotSessionTurn], list[EmmaExtractedFeatures]],
    ) -> list[EnvironmentStateTurn]:
        """Get the environment state history from a set of turns.

        Since we use the threadpool to load features, it does not naturally maintain the order.
        Therefore for each turn submitted, we also track its index to ensure the returned features
        are ordered.
        """
        # Only keep turns which have been used to change the visual frames
        relevant_turns: Iterator[SimBotSessionTurn] = (
            turn
            for turn in turns
            if turn.intent.agent and turn.intent.agent.type == SimBotIntentType.act_low_level
        )

        environment_history: dict[int, EnvironmentStateTurn] = {}

        with ThreadPoolExecutor() as executor:
            # On submitting, the future can be used a key to map to the session turn it came from
            future_to_turn: dict[Future[list[EmmaExtractedFeatures]], SimBotSessionTurn] = {
                executor.submit(extracted_features_load_fn, turn): turn for turn in relevant_turns
            }

            for future in as_completed(future_to_turn):
                turn = future_to_turn[future]
                raw_output = (
                    turn.actions.interaction.raw_output if turn.actions.interaction else None
                )
                try:
                    environment_history[turn.idx] = EnvironmentStateTurn(
                        features=future.result(), output=raw_output
                    )
                except Exception as err:
                    logger.exception("Unable to get features for the turn", exc_info=err)

        # Ensure the environment history is sorted properly and return them
        return list(dict(sorted(environment_history.items())).values())
