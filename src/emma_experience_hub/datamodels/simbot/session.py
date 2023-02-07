import itertools
from collections.abc import Iterator
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from contextlib import suppress
from datetime import datetime
from functools import cached_property
from typing import Callable, Optional, Union

from loguru import logger
from overrides import overrides
from pydantic import BaseModel, Field, root_validator, validator

from emma_experience_hub.datamodels import (
    DialogueUtterance,
    EmmaExtractedFeatures,
    EnvironmentStateTurn,
)
from emma_experience_hub.datamodels.common import Position, RotationQuaternion
from emma_experience_hub.datamodels.simbot.actions import SimBotAction, SimBotDialogAction
from emma_experience_hub.datamodels.simbot.enums import (
    SimBotActionType,
    SimBotAnyUserIntentType,
    SimBotEnvironmentIntentType,
    SimBotIntentType,
    SimBotPhysicalInteractionIntentType,
    SimBotVerbalInteractionIntentType,
)
from emma_experience_hub.datamodels.simbot.feedback import SimBotFeedbackState
from emma_experience_hub.datamodels.simbot.intents import SimBotIntent
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotAuxiliaryMetadataUri,
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

    user: Optional[SimBotAnyUserIntentType] = None
    environment: Optional[SimBotIntent[SimBotEnvironmentIntentType]] = None
    physical_interaction: Optional[SimBotIntent[SimBotPhysicalInteractionIntentType]] = None
    verbal_interaction: Optional[SimBotIntent[SimBotVerbalInteractionIntentType]] = None

    @validator("user", pre=True)
    @classmethod
    def convert_user_intent_type_enum(
        cls, intent_type: Union[str, SimBotIntentType, None]
    ) -> Union[str, SimBotIntentType, None]:
        """Check the incoming value for the intent type and ensure it will be an enum."""
        if isinstance(intent_type, str):
            # See if the intent type is already a value within the enum
            with suppress(ValueError):
                return SimBotIntentType(intent_type)

            # See if the intent type is already a key within the enum
            with suppress(KeyError):
                return SimBotIntentType[intent_type]

        # Otherwise just return it and let it error if it errors
        return intent_type

    @property
    def should_generate_interaction_action(self) -> bool:
        """Return True is the agent should generate an interaction action."""
        return self.physical_interaction is not None

    @property
    def agent_should_ask_question_to_user(self) -> bool:
        """Return True if the agent should ask for confirmation instead of just acting."""
        return (
            self.physical_interaction is not None
            and self.physical_interaction.type.triggers_question_to_user
        )

    @property
    def is_searching(self) -> bool:
        """Return True if the agent is currently searching for an object."""
        is_search = (
            self.physical_interaction is not None
            and self.physical_interaction.type == SimBotIntentType.search
        )
        return is_search

    @property
    def is_searching_after_not_seeing_object(self) -> bool:
        """Return True if the agent is searching after not directly seeing the object ."""
        is_act_no_match = (
            self.verbal_interaction is not None
            and self.verbal_interaction.type == SimBotIntentType.act_no_match
        )
        return self.is_searching and is_act_no_match

    @property
    def all_intent_types(self) -> list[SimBotIntentType]:
        """Return a list of all the intent types parsed for the turn."""
        all_intent_types: list[SimBotIntentType] = []

        if self.user:
            all_intent_types.append(self.user)
        if self.environment:
            all_intent_types.append(self.environment.type)
        if self.physical_interaction:
            all_intent_types.append(self.physical_interaction.type)
        if self.verbal_interaction:
            all_intent_types.append(self.verbal_interaction.type)

        return all_intent_types


class SimBotSessionTurnActions(BaseModel, validate_assignment=True):
    """Actions generated by the agent.

    This class constrains us to never return more than one interaction action or dialog action for
    a given turn.

    The validators are called when the attributes are assigned to, making sure that the actions
    always have the correct IDs.
    """

    interaction: Optional[SimBotAction] = None
    dialog: Optional[SimBotDialogAction] = None

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

    @property
    def any_action_failed(self) -> bool:
        """Return True if any action contains an error status."""
        is_interaction_failed = self.interaction and not self.interaction.is_successful
        is_dialog_failed = self.dialog and not self.dialog.is_successful

        return bool(is_interaction_failed or is_dialog_failed)

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

    def mark_all_as_successful(self) -> None:
        """Mark all the actions as successful, if they do not already have a status."""
        if self.interaction and not self.interaction.status:
            self.interaction.mark_as_successful()
        if self.dialog and not self.dialog.status:
            self.dialog.mark_as_successful()

    def mark_remaining_as_blocked(self) -> None:
        """Mark all actions without statuses as 'blocked', as they were never executed."""
        if self.interaction and not self.interaction.status:
            self.interaction.mark_as_blocked()
        if self.dialog and not self.dialog.status:
            self.dialog.mark_as_blocked()


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


class SimBotInventory(BaseModel, validate_assignment=True):
    """Track what is in the inventory of the SimBot agent.

    The turn_idx and action_id inform when the inventory were last updated.
    """

    entity: Optional[str] = None
    turn_idx: int = Field(default=0, ge=0, description="When the inventory was last updated.")

    @property
    def is_empty(self) -> bool:
        """Return True if the agent inventory is empty."""
        return not bool(self.entity)

    @classmethod
    def from_action(cls, action: SimBotAction, turn_idx: int) -> "SimBotInventory":
        """Instantiate an inventory from the action."""
        if action.adds_object_to_inventory and action.is_successful:
            return cls(entity=action.payload.entity_name, turn_idx=turn_idx)

        if action.removes_object_from_inventory and action.is_successful:
            return cls(entity=None, turn_idx=turn_idx)

        raise AssertionError("Action does not alter/change the inventory in any way")


class SimBotSessionState(BaseModel, validate_assignment=True):
    """Track the state of the entire session, within each turn.

    IMPORTANT: This state is copied to the newly created session turn, therefore storing anything
    in this class WILL be copied over to new turns. I recommend not storing anything here that is
    not needed in future turns.
    """

    utterance_queue: SimBotQueue[str] = SimBotQueue[str]()
    find_queue: SimBotQueue[SimBotAction] = SimBotQueue[SimBotAction]()
    inventory: SimBotInventory = SimBotInventory()


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
    state: SimBotSessionState

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
            state=SimBotSessionState(),
        )

    @property
    def utterances(self) -> list[DialogueUtterance]:
        """Get the utterances from the session turn, if any."""
        utterances: list[DialogueUtterance] = []

        # If there is a user utterance, add it first.
        if self.speech is not None:
            utterances.append(DialogueUtterance(utterance=self.speech.utterance, role="user"))

        # Do not include lightweight dialog actions within the utterances!
        if self.actions.dialog is not None:
            utterances.append(
                DialogueUtterance(utterance=self.actions.dialog.payload.value, role="agent")
            )

        return utterances

    @property
    def feedback_rule_id(self) -> Optional[int]:
        """Get the id for the rule used to generate the agent feedback for that turn."""
        if self.actions.dialog is not None:
            return self.actions.dialog.payload.rule_id

        return None

    def convert_to_simbot_response(self) -> SimBotResponse:
        """Convert the session turn to a SimBotResponse, to be returned to the API."""
        actions: list[SimBotAction] = self.actions.to_list()

        # If the agent wants to ask for confirmation before trying to act, then only return the
        # dialog action, which SHOULD have the confirmation question for the user
        if self.intent.agent_should_ask_question_to_user:
            actions = [self.actions.dialog] if self.actions.dialog is not None else []

        if not actions:
            raise AssertionError(
                "There is no action to be returned. Have you run the response generator on this?"
            )

        return SimBotResponse(
            sessionId=self.session_id,
            predictionRequestId=self.prediction_request_id,
            objectOutputType=self.actions.object_output_type,
            actions=actions,
        )

    @property
    def is_going_to_found_object_from_search(self) -> bool:
        """Return True if the agent is going to a found object from a search."""
        is_goto_object_action = (
            self.actions is not None
            and self.actions.interaction is not None
            and self.actions.interaction.is_goto_object
        )
        return self.intent.is_searching and is_goto_object_action


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
        sorted_turns = sorted(turns, key=lambda turn: turn.idx)

        logger.debug(
            f"Sorting session turns; {[turn.idx for turn in turns]} -> {[turn.idx for turn in sorted_turns]}"
        )

        return sorted_turns

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
        If it doesn't have a user intent, or the user intent is valid, then let it through the
        filter.
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
    def current_state(self) -> SimBotSessionState:
        """Return the state from the most current turn."""
        return self.current_turn.state

    @property
    def is_find_object_in_progress(self) -> bool:
        """Is the find object pipeline currently in progress?"""
        return self.current_state.find_queue.is_not_empty

    @property
    def has_found_object(self) -> bool:
        """Object has been found."""
        return (
            self.previous_valid_turn is not None
            and self.previous_valid_turn.actions.interaction is not None
            and self.previous_valid_turn.actions.interaction.type == SimBotActionType.Highlight
        )

    @property
    def inventory(self) -> SimBotInventory:
        """What object is the agent holding?"""
        return self.current_turn.state.inventory

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

    def try_to_update_agent_inventory(self) -> None:
        """Try to update the agent inventory given the actions from the previous turn."""
        if not self.previous_valid_turn:
            return

        if not self.previous_valid_turn.actions.interaction:
            return

        with suppress(AssertionError):
            self.current_turn.state.inventory = SimBotInventory.from_action(
                self.previous_valid_turn.actions.interaction, self.previous_valid_turn.idx
            )

    def to_feedback_state(self) -> SimBotFeedbackState:
        """Convert the session to the simplified state."""
        return SimBotFeedbackState.from_all_information(
            num_turns=len(self.turns),
            current_room=self.current_turn.environment.current_room,
            user_intent_type=self.current_turn.intent.user,
            environment_intent=self.current_turn.intent.environment,
            physical_interaction_intent=self.current_turn.intent.physical_interaction,
            verbal_interaction_intent=self.current_turn.intent.verbal_interaction,
            interaction_action=self.current_turn.actions.interaction,
            current_room_per_turn=[turn.environment.current_room for turn in self.turns],
            interaction_action_per_turn=[
                turn.actions.interaction for turn in self.turns if turn.actions.interaction
            ],
            intent_types_per_turn=[turn.intent.all_intent_types for turn in self.turns],
            utterance_queue_not_empty=self.current_state.utterance_queue.is_not_empty,
            find_queue_not_empty=self.current_state.find_queue.is_not_empty,
            previous_find_queue_not_empty=self.previous_turn.state.find_queue.is_not_empty
            if self.previous_turn
            else False,
            used_rule_ids=self._get_used_feedback_rule_ids(),
            inventory_turn=self.inventory.turn_idx,
            inventory_entity=self.inventory.entity,
        )

    @staticmethod
    def get_dialogue_history_from_session_turns(  # noqa: WPS602
        turns: list[SimBotSessionTurn], *, include_agent_responses: bool = True
    ) -> list[DialogueUtterance]:
        """Get a dialogue history from the given turns."""
        utterances_lists = (turn.utterances for turn in turns)
        dialogue_history: Iterator[DialogueUtterance] = itertools.chain.from_iterable(
            utterances_lists
        )

        # Remvoe agent responses if they are not desired
        if not include_agent_responses:
            dialogue_history = (
                utterance for utterance in dialogue_history if utterance.role != "agent"
            )

        return list(dialogue_history)

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
            if turn.intent.physical_interaction
            and turn.intent.physical_interaction.type == SimBotIntentType.act_one_match
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

    def _get_used_feedback_rule_ids(self) -> list[int]:
        """Get all the rule IDs that were used to generate responses."""
        rule_ids = [
            turn.feedback_rule_id for turn in self.turns if turn.feedback_rule_id is not None
        ]
        return rule_ids
