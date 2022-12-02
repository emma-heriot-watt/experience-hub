from typing import Optional, cast

from pydantic import BaseModel, Field

from emma_experience_hub.datamodels.simbot.actions import SimBotAction, SimBotActionStatus
from emma_experience_hub.datamodels.simbot.enums import SimBotActionType
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotAuxiliaryMetadataPayload,
    SimBotSpeechRecognitionPayload,
)


class SimBotRequestHeader(BaseModel):
    """SimBot request headers, which must exist for each request."""

    session_id: str = Field(..., alias="sessionId")
    prediction_request_id: str = Field(..., alias="predictionRequestId")


class SimBotRequestBody(BaseModel):
    """Request body from the SimBot game engine."""

    sensors: list[SimBotAction]
    previous_actions: list[SimBotActionStatus] = Field(..., alias="previousActions")

    @property
    def has_previous_action_status(self) -> bool:
        """Does the request contain the status of previous actions?"""
        return bool(len(self.previous_actions))


class SimBotRequest(BaseModel, extra="allow"):
    """Request from the SimBot server.

    FastAPI will directly parse the JSON body into this Pydantic model.
    """

    header: SimBotRequestHeader
    request: SimBotRequestBody

    @property
    def auxiliary_metadata(self) -> SimBotAuxiliaryMetadataPayload:
        """Easily get the game metadata."""
        return cast(
            SimBotAuxiliaryMetadataPayload,
            self._easily_get_action_from_sensors(SimBotActionType.GameMetaData).payload,
        )

    @property
    def speech_recognition(self) -> Optional[SimBotSpeechRecognitionPayload]:
        """Easily get the speech recognition action."""
        try:
            return cast(
                SimBotSpeechRecognitionPayload,
                self._easily_get_action_from_sensors(SimBotActionType.SpeechRecognition).payload,
            )
        except Exception:
            return None

    def _easily_get_action_from_sensors(self, action_type: SimBotActionType) -> SimBotAction:
        """Easily get the action for the given action type from the sensors."""
        for sensor in self.request.sensors:
            if sensor.type == action_type:
                return sensor

        raise AssertionError(f"{action_type} not found in the sensors list.")
