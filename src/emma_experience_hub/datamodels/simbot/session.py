import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import suppress
from datetime import datetime
from typing import Callable, Optional, cast

from pydantic import BaseModel, validator

from emma_experience_hub.common.logging import get_logger
from emma_experience_hub.datamodels.emma import (
    DialogueUtterance,
    EmmaExtractedFeatures,
    EnvironmentStateTurn,
)
from emma_experience_hub.datamodels.simbot.actions import (
    SimBotAction,
    SimBotActionStatus,
    SimBotActionType,
)
from emma_experience_hub.datamodels.simbot.intents import SimBotIntent, SimBotIntentType
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotAuxiliaryMetadataUri,
    SimBotSpeechRecognitionPayload,
)
from emma_experience_hub.datamodels.simbot.payloads.dialog import SimBotDialogPayload
from emma_experience_hub.datamodels.simbot.request import SimBotRequest
from emma_experience_hub.datamodels.simbot.response import SimBotResponse


logger = get_logger()


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
    action: Optional[SimBotAction] = None
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
    def has_intent(self) -> bool:
        """Determine whether or not the turn has an extracted intent."""
        return self.intent is not None

    @property
    def is_instruction_intent(self) -> bool:
        """Is the turn an instruction?"""
        return self.intent is not None and self.intent.type == SimBotIntentType.instruction

    @property
    def is_end_of_trajectory_intent(self) -> bool:
        """Is the turn at the end of a trajectory?"""
        return self.intent is not None and self.intent.type == SimBotIntentType.end_of_trajectory

    @property
    def has_action(self) -> bool:
        """Determine whether or not the turn has generated an action."""
        return self.action is not None

    @property
    def action_status(self) -> Optional[SimBotActionStatus]:
        """Return the status of the action is available."""
        if self.action is None or self.action.status is None:
            return None

        return self.action.status

    @property
    def utterances(self) -> list[DialogueUtterance]:
        """Get the utterances from the session turn, if any."""
        utterances = []

        # If there is a user utterance, add it first.
        if self.speech is not None:
            utterances.append(
                DialogueUtterance(
                    utterance=self.speech.utterance,
                    role="user",
                    intent=self.intent.type.name if self.intent else None,
                )
            )

        if self.action is not None:
            if self.action.type == SimBotActionType.Dialog:
                payload = cast(SimBotDialogPayload, self.action.payload)
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
        if not self.action:
            raise AssertionError(
                "There is no action to be returned. Have you run the response generator on this?"
            )

        return SimBotResponse(
            sessionId=self.session_id,
            predictionRequestId=self.prediction_request_id,
            objectOutputType="OBJECT_CLASS",
            actions=[self.action],
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

    def get_turns_from_most_recent_instruction(self) -> list[SimBotSessionTurn]:
        """Get all the session turns from the most recent instruction utterance."""
        # Determine whether each turn has an instruction intent
        session_turn_has_instruction_intent = [turn.is_instruction_intent for turn in self.turns]

        # Determine whether each turns has a end of trajectory intent
        session_turn_has_end_of_trajectory_intent = [
            turn.is_end_of_trajectory_intent for turn in self.turns
        ]

        # Set the cutoff index to 0, so all turns will be returned
        turn_cutoff_index = 0

        # Get the index of the most recent turn with an instruction index
        # i.e. the last index is the first index from the reversed list
        with suppress(ValueError):
            turn_cutoff_index = (
                len(session_turn_has_instruction_intent)
                - session_turn_has_instruction_intent[::-1].index(True)
                - 1
            )

        # Check if there are any "end of trajectory" intents after the index
        if any(session_turn_has_end_of_trajectory_intent[turn_cutoff_index:]):
            # If there are end of trajectory intents after the index, get the new index as the turn
            # AFTER the last "end of trajectory" intent
            with suppress(ValueError):
                turn_cutoff_index = len(
                    session_turn_has_end_of_trajectory_intent
                ) - session_turn_has_end_of_trajectory_intent[::-1].index(True)

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
        environment_history: dict[int, EnvironmentStateTurn] = {}

        with ThreadPoolExecutor() as executor:
            future_to_session_turn = {
                executor.submit(
                    extracted_features_load_fn, turn.session_id, turn.prediction_request_id
                ): turn
                for turn in turns
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
