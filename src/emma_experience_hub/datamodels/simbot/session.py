from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator

from emma_experience_hub.datamodels.simbot.intents import SimBotIntent
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotAuxiliaryMetadataUri,
    SimBotSpeechRecognitionPayload,
)
from emma_experience_hub.datamodels.simbot.request import SimBotRequest


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

    speech: SimBotSpeechRecognitionPayload

    # URI to the auxiliary metadata file, as provided by the SimBot Arena
    auxiliary_metadata_uri: SimBotAuxiliaryMetadataUri

    intent: Optional[SimBotIntent] = None

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
        raise NotImplementedError()

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
