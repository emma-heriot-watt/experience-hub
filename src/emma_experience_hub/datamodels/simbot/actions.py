from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, root_validator, validator

from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotAuxiliaryMetadataPayload,
    SimBotDialogPayload,
    SimBotGotoPayload,
    SimBotLookPayload,
    SimbotMovePayload,
    SimBotNavigationPayload,
    SimBotObjectInteractionPayload,
    SimBotRotatePayload,
    SimBotSpeechRecognitionPayload,
)


# List of action types, taken from the example inference server
SimBotNavigationActionType = Literal[
    "Goto",
    "Move",
    "Rotate",
    "Look",
    # "CameraChange",
]
SimBotObjectInteractionActionType = Literal[
    "Pickup",
    "Open",
    "Close",
    "Break",
    "Scan",
    "Examine",
    "Place",
    "Pour",
    "Toggle",
    "Fill",
    "Clean",
    # "Burn",
    # "Slice",
    # "Throw",
    # "Use",
]
SimBotLanguageActionType = Literal["Dialog", "SpeechRecognition"]
SimBotOtherActionType = Literal["GameMetaData"]

SimBotActionType = Literal[
    SimBotNavigationActionType,
    SimBotObjectInteractionActionType,
    SimBotLanguageActionType,
    SimBotOtherActionType,
]

SIMBOT_ACTION_TYPE_TO_KEY_MAPPING: Mapping[SimBotActionType, str] = MappingProxyType(
    {
        # Sensors
        "SpeechRecognition": "recognition",
        "GameMetaData": "metaData",
        # Dialog
        "Dialog": "dialog",
        # Navigation
        "Goto": "goto",
        "Move": "move",
        "Rotate": "rotation",
        "Look": "look",
        # Object interaction
        "Pickup": "pickup",
        "Open": "open",
        "Close": "close",
        "Break": "break",
        "Scan": "scan",
        "Examine": "examine",
        "Place": "place",
        "Pour": "pour",
        "Toggle": "toggle",
        "Fill": "fill",
        "Clean": "clean",
    }
)

SimBotPayload = Union[
    SimBotSpeechRecognitionPayload,
    SimBotAuxiliaryMetadataPayload,
    SimBotDialogPayload,
    SimBotGotoPayload,
    SimbotMovePayload,
    SimBotRotatePayload,
    SimBotLookPayload,
    SimBotObjectInteractionPayload,
    SimBotNavigationPayload,
]

SimBotActionTypePayloadModelMap: Mapping[SimBotActionType, type[SimBotPayload]] = MappingProxyType(
    {
        # Sensors
        "SpeechRecognition": SimBotSpeechRecognitionPayload,
        "GameMetaData": SimBotAuxiliaryMetadataPayload,
        # Dialog
        "Dialog": SimBotDialogPayload,
        # Navigation
        "Goto": SimBotGotoPayload,
        "Move": SimbotMovePayload,
        "Rotate": SimBotRotatePayload,
        "Look": SimBotLookPayload,
        # Object interaction
        "Pickup": SimBotObjectInteractionPayload,
        "Open": SimBotObjectInteractionPayload,
        "Close": SimBotObjectInteractionPayload,
        "Break": SimBotObjectInteractionPayload,
        "Scan": SimBotObjectInteractionPayload,
        "Examine": SimBotObjectInteractionPayload,
        "Place": SimBotObjectInteractionPayload,
        "Pour": SimBotObjectInteractionPayload,
        "Toggle": SimBotObjectInteractionPayload,
        "Fill": SimBotObjectInteractionPayload,
        "Clean": SimBotObjectInteractionPayload,
    }
)


class SimBotActionStatusType(Enum):
    """Possible action status types returned from subsequent requests."""

    action_successful = "ActionSuccessful"
    unsupported_action = "UnsupportedAction"
    unsupported_navigation = "UnsupportedNavigation"
    already_holding_object = "AlreadyHoldingObject"
    receptacle_is_full = "ReceptacleIsFull"
    receptacle_is_closed = "ReceptacleIsClosed"
    target_inaccessible = "TargetInaccessible"
    killed_by_hazard = "KilledByHazard"
    target_out_of_range = "TargetOutOfRange"
    alternative_navigation_used = "AlternativeNavigationUsed"
    interrupted_by_new_command_batch = "InterruptedByNewCommandBatch"
    raycast_missed = "RaycastMissed"
    object_unpowered = "ObjectUnpowered"
    object_overloaded = "ObjectOverloaded"
    no_free_hand = "NoFreeHand"
    invalid_command = "InvalidCommand"
    object_not_picked_up = "ObjectNotPickedUp"

    @classmethod
    def reverse_mapping(cls) -> dict[str, str]:
        """Create a reversed mapping of the enum."""
        return {element.value: element.name for element in cls}

    @classmethod
    def from_value(cls, value: str) -> "SimBotActionStatusType":  # noqa: WPS110
        """Instantiate the enum from the value of the enum."""
        return cls[cls.reverse_mapping()[value]]


class SimBotActionStatus(BaseModel):
    """Status of the previous action taken."""

    id: str
    type: SimBotActionType
    success: bool
    error_type: SimBotActionStatusType = Field(..., alias="errorType")

    @validator("error_type", pre=True)
    @classmethod
    def convert_error_type_enum(cls, error_type: str) -> str:
        """Check the incoming value for the error type and ensure it will be an enum.

        If the error type is one of the enum values, convert it to the correct enum name so that it
        will parse properly.
        """
        reverse_mapping = SimBotActionStatusType.reverse_mapping()

        correct_error_type = (
            error_type if error_type in reverse_mapping else reverse_mapping[error_type]
        )

        return correct_error_type


class SimBotAction(BaseModel, extra="allow"):
    """Common SimBot Action which can parse the fields into the specific actions.

    To instantiate the action manually (without using the helper parsers), provide the action
    payload to the `payload` field.

    The `payload` field will _never_ be exported. However, the correct key for the field --- i.e.,
    whatever is expected by the response --- will be. This logic is all outlined within the
    `check_payload_exists_for_all_necessary_keys()` class method.
    """

    type: SimBotActionType
    payload: SimBotPayload = Field(..., exclude=True)
    status: Optional[SimBotActionStatus] = None

    @root_validator(pre=True)
    @classmethod
    def check_payload_exists_for_all_necessary_keys(
        cls, values: dict[str, Any]  # noqa: WPS110
    ) -> dict[str, Any]:
        """Check the payload for the stated action type exist."""
        # Get the action type
        action_type = values["type"]

        # Get the correct key for the action payload
        payload_key = SIMBOT_ACTION_TYPE_TO_KEY_MAPPING[action_type]

        # Get the payload from either the `payload` field or the field for the payload_key
        payload = values.get("payload", values.get(payload_key))

        if payload is None:
            raise AssertionError(
                f"For the given action type `{action_type}`, the expected key for the payload (`{payload_key}`) is not found.",
                f"Available keys: {list(values.keys())}",
            )

        # Parse the payload into the correct instance if necessary
        parsed_payload = (
            payload
            if isinstance(payload, BaseModel)
            else SimBotActionTypePayloadModelMap[action_type].parse_obj(values[payload_key])
        )

        # Set the payload for both the fields
        values[payload_key] = parsed_payload
        values["payload"] = parsed_payload

        return values

    @property
    def is_status_known(self) -> bool:
        """Do we know the outcome of the action?"""
        return self.status is not None

    @property
    def is_successful(self) -> bool:
        """Is the action successful?"""
        if self.status is not None:
            return self.status.success

        return False
