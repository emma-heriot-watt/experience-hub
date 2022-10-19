import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import suppress
from datetime import datetime
from typing import Callable, Optional, cast

from loguru import logger
from pydantic import BaseModel, validator

from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN
from emma_experience_hub.datamodels.emma import (
    DialogueUtterance,
    EmmaExtractedFeatures,
    EnvironmentStateTurn,
)
from emma_experience_hub.datamodels.simbot.actions import SimBotAction, SimBotActionType
from emma_experience_hub.datamodels.simbot.intents import SimBotIntent, SimBotIntentType
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotAuxiliaryMetadataUri,
    SimBotDialogPayload,
    SimBotObjectOutputType,
    SimBotSpeechRecognitionPayload,
)
from emma_experience_hub.datamodels.simbot.request import SimBotRequest
from emma_experience_hub.datamodels.simbot.response import SimBotResponse


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


class SimBotSessionTurn(BaseModel):
    """Current turn for a SimBot game session."""

    session_id: str
    prediction_request_id: str
    idx: int

    timestamp: SimBotSessionTurnTimestamp

    current_room: str
    unique_room_names: set[str]
    viewpoints: set[str]

    speech: Optional[SimBotSpeechRecognitionPayload] = None

    # URI to the auxiliary metadata file, as provided by the SimBot Arena
    auxiliary_metadata_uri: SimBotAuxiliaryMetadataUri

    intent: Optional[SimBotIntent] = None
    actions: Optional[list[SimBotAction]] = None
    raw_output: Optional[str] = None

    @classmethod
    def new_from_simbot_request(cls, request: SimBotRequest, idx: int) -> "SimBotSessionTurn":
        """Create a session turn from a SimBotRequest."""
        return cls(
            session_id=request.header.session_id,
            prediction_request_id=request.header.prediction_request_id,
            idx=idx,
            timestamp=SimBotSessionTurnTimestamp(),
            current_room=request.auxiliary_metadata.current_room,
            unique_room_names=request.auxiliary_metadata.unique_room_names,
            viewpoints=request.auxiliary_metadata.viewpoints,
            speech=request.speech_recognition,
            auxiliary_metadata_uri=request.auxiliary_metadata.uri,
        )

    @property
    def is_instruction_intent(self) -> bool:
        """Is the turn an instruction?"""
        return self.intent is not None and self.intent.type == SimBotIntentType.instruction

    @property
    def is_clarify_intent(self) -> bool:
        """Does the turn result in a clarification question?"""
        return self.intent is not None and self.intent.type.is_clarification_question

    @property
    def is_actionable_intent(self) -> bool:
        """Is the incoming utterance an actionable intent?"""
        return self.intent is not None and self.intent.type.is_actionable

    @property
    def output_contains_end_of_trajectory_token(self) -> bool:
        """Return True if the raw output contains the special token for end of trajectory.

        This also checks that the raw output was generated from the action prediction model by
        ensuring that the intent type is an instruction. This is just in case the ASR breaks or
        something --- we don't want Litte Bobby Tables (https://xkcd.com/327) breaking things.
        """
        return (
            self.intent is not None
            and self.intent.type == SimBotIntentType.instruction
            and self.raw_output is not None
            and END_OF_TRAJECTORY_TOKEN in self.raw_output
        )

    @property
    def object_output_type(self) -> Optional[SimBotObjectOutputType]:
        """Get the object output type used by the actions.

        If there are more than one type in the list, we have a problem.
        """
        if not self.actions:
            return None

        output_types = {
            action.object_output_type
            for action in self.actions
            if action.object_output_type is not None
        }

        if not output_types:
            return None

        if len(output_types) > 1:
            raise AssertionError(
                "There is more than one output type in this list. That will breka the response. We should not be returning more than one object-related interaction action per turn."
            )

        return next(iter(output_types))

    @property
    def all_actions_are_successful(self) -> bool:
        """Return the status of the action is available."""
        if self.actions is None:
            return False

        return all([action.is_successful for action in self.actions])

    @property
    def utterances(self) -> list[DialogueUtterance]:
        """Get the utterances from the session turn, if any."""
        utterances: list[DialogueUtterance] = []

        # If there is a user utterance, add it first.
        if self.speech is not None:
            utterances.append(
                DialogueUtterance(
                    utterance=self.speech.utterance,
                    role="user",
                    intent=self.intent.type.name if self.intent else None,
                )
            )

        if self.actions is not None:
            dialog_actions = (
                action for action in self.actions if action.type == SimBotActionType.Dialog
            )

            for action in dialog_actions:
                payload = cast(SimBotDialogPayload, action.payload)
                utterances.append(
                    DialogueUtterance(
                        utterance=payload.value,
                        role="agent",
                        intent=payload.intent.name if payload.intent else None,
                    )
                )

        return utterances

    def convert_to_simbot_response(self) -> SimBotResponse:
        """Convert the session turn to a SimBotResponse, to be returned to the API."""
        if not self.actions:
            raise AssertionError(
                "There is no action to be returned. Have you run the response generator on this?"
            )

        # Default to OBJECT_MASK as the object output type if there is None
        object_output_type = (
            self.object_output_type
            if self.object_output_type
            else SimBotObjectOutputType.object_mask
        )

        return SimBotResponse(
            sessionId=self.session_id,
            predictionRequestId=self.prediction_request_id,
            objectOutputType=object_output_type,
            actions=self.actions,
        )

    def load_features(
        self, load_fn: Callable[[str, str], list[EmmaExtractedFeatures]]
    ) -> list[EmmaExtractedFeatures]:
        """Load the features for the given turn.

        Provide the field with the `load` method from the cache client and it should return the
        features.
        """
        return load_fn(self.session_id, self.prediction_request_id)


class SimBotSession(BaseModel):
    """A single SimBot Game Session."""

    session_id: str

    turns: list[SimBotSessionTurn]

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
    def num_turns(self) -> int:
        """Get the number of turns taken within the session."""
        return len(self.turns)

    @property
    def current_turn(self) -> SimBotSessionTurn:
        """Get the current turn being handled."""
        return self.turns[-1]

    @property
    def start_time(self) -> datetime:
        """Get the datetime of when the session started."""
        return self.turns[0].timestamp.start

    @property
    def end_time(self) -> Optional[datetime]:
        """If it exists, get the end time of the session.

        If the last turn does not have an endtime, then it means that the turn is likely currently
        being processed.
        """
        return self.turns[-1].timestamp.end

    def get_turns_since_local_state_reset(self) -> list[SimBotSessionTurn]:
        """Get all the session turns from the most-recent local state reset.

        This can occur after an instruction.
        """
        is_cut_off_turn = [self._should_turn_reset_local_state(turn) for turn in self.turns]

        # Set the cutoff index to 0, so all turns will be returned by default
        turn_cutoff_index = 0

        # Get the index of the most recent turn with an instruction index
        # i.e. the last index is the first index from the reversed list
        with suppress(ValueError):
            turn_cutoff_index = len(is_cut_off_turn) - is_cut_off_turn[::-1].index(True) - 1

        # Return all the turns after the cutoff point
        return self.turns[turn_cutoff_index:]

    def get_dialogue_history(self, turns: list[SimBotSessionTurn]) -> list[DialogueUtterance]:
        """Get a dialogue history from the given turns."""
        utterances_lists = (turn.utterances for turn in turns)
        dialogue_history = list(itertools.chain.from_iterable(utterances_lists))
        return dialogue_history

    def get_environment_state_history(
        self,
        turns: list[SimBotSessionTurn],
        extracted_features_load_fn: Callable[[str, str], list[EmmaExtractedFeatures]],
    ) -> list[EnvironmentStateTurn]:
        """Get the environment state history from a set of turns.

        This also loads the extracted features from the cache.
        """
        # Only keep turns which have been used to change the visual frames
        instruction_turns = (turn for turn in turns if turn.is_instruction_intent)

        # Use thread pool to load the features from the files, but it will not maintain the order
        environment_history: dict[int, EnvironmentStateTurn] = {}

        with ThreadPoolExecutor() as executor:
            future_to_session_turn = {
                executor.submit(
                    extracted_features_load_fn, turn.session_id, turn.prediction_request_id
                ): turn
                for turn in instruction_turns
            }

            for future in as_completed(future_to_session_turn):
                turn = future_to_session_turn[future]
                try:
                    environment_history[turn.idx] = EnvironmentStateTurn(
                        features=future.result(), output=turn.raw_output
                    )
                except Exception as err:
                    logger.exception("Unable to get features for the turn", exc_info=err)

        # Ensure the environment history is sorted properly and return them
        return list(dict(sorted(environment_history.items())).values())

    def _should_turn_reset_local_state(self, turn: SimBotSessionTurn) -> bool:
        """Determine whether the given turn is at the start of a new sequence of actions.

        Essentially, should all the turns before this one be ignored when providing data to the
        neural services?
        """
        conditions = [
            # If the current turn is at the start of the interaction
            turn.idx == 0,
            # If the current turn is the only one
            len(self.turns) == 1,
            # If the user has said something that resulted in a clarification question
            turn.speech is not None and turn.is_clarify_intent,
            # if the user said something that resulted in the model being able to act directly,
            # and it did not follow another utterance
            turn.speech is not None
            and turn.is_instruction_intent
            and turn.idx > 0
            and self.turns[turn.idx - 1].speech is None,
            # If the user interrupts the action sequence directly after the model predicts an end
            # of trajectory token but was not able to return a dialog action for it
            turn.speech is not None
            and turn.idx > 0
            and self.turns[turn.idx - 1].output_contains_end_of_trajectory_token,
            # If the user interrupts the action sequence before we are able to predict the end of
            # trajectory token
            turn.speech is not None
            and turn.idx > 0
            and not self.turns[turn.idx - 1].output_contains_end_of_trajectory_token
            and self.turns[turn.idx - 1].is_instruction_intent,
            # If the current turn comes after the previous turn was a non-actionable intent
            turn.speech is not None
            and turn.idx > 0
            and not self.turns[turn.idx - 1].is_actionable_intent,
        ]

        return any(conditions)
