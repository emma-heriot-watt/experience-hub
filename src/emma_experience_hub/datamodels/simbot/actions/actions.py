from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, root_validator, validator

from emma_experience_hub.datamodels.simbot.actions.auxiliary_metadata import (
    SimBotAuxiliaryMetadataAction,
)
from emma_experience_hub.datamodels.simbot.actions.dialog import SimBotDialogAction
from emma_experience_hub.datamodels.simbot.actions.navigation import (
    SimBotGotoAction,
    SimBotLookAction,
    SimbotMoveAction,
    SimBotRotateAction,
)
from emma_experience_hub.datamodels.simbot.actions.object_interaction import (
    SimBotObjectInteractionAction,
)
from emma_experience_hub.datamodels.simbot.actions.speech_recognition import (
    SimBotSpeechRecognitionAction,
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

SIMBOT_ACTION_TYPE_TO_MODEL_MAPPING: Mapping[SimBotActionType, type[BaseModel]] = MappingProxyType(
    {
        # Sensors
        "SpeechRecognition": SimBotSpeechRecognitionAction,
        "GameMetaData": SimBotAuxiliaryMetadataAction,
        # Dialog
        "Dialog": SimBotDialogAction,
        # Navigation
        "Goto": SimBotGotoAction,
        "Move": SimbotMoveAction,
        "Rotate": SimBotRotateAction,
        "Look": SimBotLookAction,
        # Object interaction
        "Pickup": SimBotObjectInteractionAction,
        "Open": SimBotObjectInteractionAction,
        "Close": SimBotObjectInteractionAction,
        "Break": SimBotObjectInteractionAction,
        "Scan": SimBotObjectInteractionAction,
        "Examine": SimBotObjectInteractionAction,
        "Place": SimBotObjectInteractionAction,
        "Pour": SimBotObjectInteractionAction,
        "Toggle": SimBotObjectInteractionAction,
        "Fill": SimBotObjectInteractionAction,
        "Clean": SimBotObjectInteractionAction,
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
    """Common SimBot Action which can parse the fields into the specific actions."""

    type: SimBotActionType
    status: Optional[SimBotActionStatus] = None

    @root_validator(pre=True)
    @classmethod
    def check_action_details(cls, values: dict[str, Any]) -> dict[str, Any]:  # noqa: WPS110
        """Check the correct details for the stated action type exist."""
        action_type = values["type"]
        action_details_key = SIMBOT_ACTION_TYPE_TO_KEY_MAPPING[action_type]
        action_details = values.get(action_details_key)

        if action_details is None:
            raise AssertionError(
                f"For the given action type `{action_type}`, the expected key for the details (`{action_details_key}`) is not found.",
                f"Available keys: {list(values.keys())}",
            )

        # Attempt to parse action details to ensure no errors
        values[action_details_key] = SIMBOT_ACTION_TYPE_TO_MODEL_MAPPING[action_type].parse_obj(
            values[action_details_key]
        )

        return values

    @property
    def details(self) -> BaseModel:
        """Get the details for the current action type without needing to know correct key."""
        attribute_name_for_action = SIMBOT_ACTION_TYPE_TO_KEY_MAPPING[self.type]
        return getattr(self, attribute_name_for_action)

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
