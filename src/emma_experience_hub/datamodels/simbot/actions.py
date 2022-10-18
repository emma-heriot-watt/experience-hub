from contextlib import suppress
from enum import Enum
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, root_validator, validator

from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotAuxiliaryMetadataPayload,
    SimBotDialogPayload,
    SimBotGotoPayload,
    SimBotLookAroundPayload,
    SimBotLookDownPayload,
    SimBotLookPayload,
    SimBotLookUpPayload,
    SimBotMoveBackwardPayload,
    SimBotMoveForwardPayload,
    SimBotMovePayload,
    SimBotObjectInteractionPayload,
    SimBotPayload,
    SimBotRotateLeftPayload,
    SimBotRotatePayload,
    SimBotRotateRightPayload,
    SimBotSpeechRecognitionPayload,
    SimBotTurnAroundPayload,
)


class SimBotActionType(Enum):
    """All action types from the SimBot Arena."""

    # Navigation
    Goto = "goto"  # noqa: WPS115
    Move = "move"  # noqa: WPS115
    Rotate = "rotation"  # noqa: WPS115
    Look = "look"  # noqa: WPS115
    # CameraChange = "camerachange"

    # Navigation Aliases (commonly used action types)
    MoveForward = "move forward"  # noqa: WPS115
    MoveBackward = "move backward"  # noqa: WPS115
    RotateLeft = "rotate left"  # noqa: WPS115
    RotateRight = "rotate right"  # noqa: WPS115
    LookUp = "look up"  # noqa: WPS115
    LookDown = "look down"  # noqa: WPS115
    LookAround = "look around"  # noqa: WPS115
    TurnAround = "turn around"  # noqa: WPS115

    # Object interaction
    Pickup = "pickup"  # noqa: WPS115
    Open = "open"  # noqa: WPS115
    Close = "close"  # noqa: WPS115
    Break = "break"  # noqa: WPS115
    Scan = "scan"  # noqa: WPS115
    Examine = "examine"  # noqa: WPS115
    Place = "place"  # noqa: WPS115
    Pour = "pour"  # noqa: WPS115
    Toggle = "toggle"  # noqa: WPS115
    Fill = "fill"  # noqa: WPS115
    Clean = "clean"  # noqa: WPS115
    # Burn = "burn"
    # Slice = "slice"
    # Throw = "throw"
    # Use = "use"

    # Language
    Dialog = "dialog"  # noqa: WPS115
    SpeechRecognition = "recognition"  # noqa: WPS115

    # Other
    GameMetaData = "metaData"  # noqa: WPS115

    @classmethod
    def navigation(cls) -> list["SimBotActionType"]:
        """Get all navigation action types from the SimBot Arena."""
        return [
            SimBotActionType.Goto,
            SimBotActionType.Move,
            SimBotActionType.Rotate,
            SimBotActionType.Look,
            SimBotActionType.MoveForward,
            SimBotActionType.MoveBackward,
            SimBotActionType.RotateLeft,
            SimBotActionType.RotateRight,
            SimBotActionType.LookUp,
            SimBotActionType.LookDown,
            SimBotActionType.LookAround,
            SimBotActionType.TurnAround,
        ]

    @classmethod
    def low_level_navigation(cls) -> list["SimBotActionType"]:
        """Get all the low-level navigation action types.

        All of these have pre-instantiated payloads too.
        """
        return [
            SimBotActionType.MoveForward,
            SimBotActionType.MoveBackward,
            SimBotActionType.RotateLeft,
            SimBotActionType.RotateRight,
            SimBotActionType.LookUp,
            SimBotActionType.LookDown,
            SimBotActionType.LookAround,
            SimBotActionType.TurnAround,
        ]

    @classmethod
    def object_interaction(cls) -> list["SimBotActionType"]:
        """Get all object interaction action types from the SimBot Arena."""
        return [
            SimBotActionType.Pickup,
            SimBotActionType.Open,
            SimBotActionType.Close,
            SimBotActionType.Break,
            SimBotActionType.Scan,
            SimBotActionType.Examine,
            SimBotActionType.Place,
            SimBotActionType.Pour,
            SimBotActionType.Toggle,
            SimBotActionType.Fill,
            SimBotActionType.Clean,
        ]

    @classmethod
    def language(cls) -> list["SimBotActionType"]:
        """Get all language action types from the SimBot Arena."""
        return [SimBotActionType.Dialog, SimBotActionType.SpeechRecognition]

    @classmethod
    def action_type_to_payload_model(cls) -> dict[str, type[SimBotPayload]]:
        """Get a map from each action type to the payload model."""
        switcher: dict[str, type[SimBotPayload]] = {
            # Sensors
            "SpeechRecognition": SimBotSpeechRecognitionPayload,
            "GameMetaData": SimBotAuxiliaryMetadataPayload,
            # Dialog
            "Dialog": SimBotDialogPayload,
            # Navigation
            "Goto": SimBotGotoPayload,
            "Move": SimBotMovePayload,
            "Rotate": SimBotRotatePayload,
            "Look": SimBotLookPayload,
            # Navigation Aliases
            "MoveForward": SimBotMoveForwardPayload,
            "MoveBackward": SimBotMoveBackwardPayload,
            "RotateLeft": SimBotRotateLeftPayload,
            "RotateRight": SimBotRotateRightPayload,
            "LookUp": SimBotLookUpPayload,
            "LookDown": SimBotLookDownPayload,
            "LookAround": SimBotLookAroundPayload,
            "TurnAround": SimBotTurnAroundPayload,
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
        return switcher

    @classmethod
    def move_actions(cls) -> set["SimBotActionType"]:
        """Return all the move forward actions."""
        return {SimBotActionType.MoveForward, SimBotActionType.MoveBackward}

    @classmethod
    def look_actions(cls) -> set["SimBotActionType"]:
        """Return all the look actions."""
        return {
            SimBotActionType.LookAround,
            SimBotActionType.LookDown,
            SimBotActionType.LookUp,
        }

    @classmethod
    def rotate_actions(cls) -> set["SimBotActionType"]:
        """Return all the rotate actions."""
        return {
            SimBotActionType.RotateLeft,
            SimBotActionType.RotateRight,
            SimBotActionType.TurnAround,
        }

    @property
    def base_type(self) -> "SimBotActionType":
        """Given a specific type, returns the base Simbot action type."""
        if self in self.move_actions():
            return SimBotActionType.Move

        if self in self.look_actions():
            return SimBotActionType.Look

        if self in self.rotate_actions():
            return SimBotActionType.Rotate

        return self

    @property
    def payload_model(self) -> type[SimBotPayload]:
        """Get the corresponding payload for the SimBot action type."""
        return self.action_type_to_payload_model()[self.name]


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
    incorrect_action_format = "IncorrectActionFormat"

    @classmethod
    def reverse_mapping(cls) -> dict[str, str]:
        """Create a reversed mapping of the enum."""
        return {element.value: element.name for element in cls}


class SimBotActionStatus(BaseModel):
    """Status of the previous action taken."""

    id: Optional[str]
    type: SimBotActionType
    success: bool
    error_type: SimBotActionStatusType = Field(..., alias="errorType")

    @validator("type", pre=True)
    @classmethod
    def convert_action_type_enum(cls, action_type: str) -> str:
        """Check the incoming value for the action type and ensure it will be an enum."""
        # See if the action type is already a value within the enum
        with suppress(ValueError):
            return SimBotActionType(action_type).value

        # See if the action type is already a key within the enum
        with suppress(KeyError):
            return SimBotActionType[action_type].value

        # Otherwise just return it and let it error if it errors
        return action_type

    @validator("error_type", pre=True)
    @classmethod
    def convert_error_type_enum(cls, error_type: str) -> str:
        """Check the incoming value for the error type and ensure it will be an enum."""
        # See if the error type is already a value within the enum
        with suppress(ValueError):
            return SimBotActionStatusType(error_type).value

        # See if the error type is already a key within the enum
        with suppress(KeyError):
            return SimBotActionStatusType[error_type].value

        # Otherwise just return it and let it error if it errors
        return error_type


class SimBotAction(BaseModel):
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
    object_output_type: Literal["OBJECT_CLASS", "OBJECT_MASK"] = "OBJECT_MASK"

    class Config:
        """Config for the model."""

        extra = "allow"
        json_encoders = {
            SimBotActionType: lambda action_type: action_type.name,
        }

    @root_validator(pre=True)
    @classmethod
    def check_payload_exists_for_all_necessary_keys(
        cls, values: dict[str, Any]  # noqa: WPS110
    ) -> dict[str, Any]:
        """Check the payload for the stated action type exist."""
        raw_action_type = values.get("type")

        if isinstance(raw_action_type, SimBotActionType):
            action_type = raw_action_type
        elif isinstance(raw_action_type, str):
            try:
                action_type = SimBotActionType[raw_action_type]
            except KeyError:
                action_type = SimBotActionType(raw_action_type)
        else:
            raise AssertionError("Unknown action type")

        # Get the correct key for the action payload
        payload_key = action_type.value.strip()

        # Get the payload from either the `payload` field or the field for the payload_key
        payload: Union[SimBotPayload, dict[str, Any], None] = values.get(
            "payload", values.get(payload_key)
        )

        if payload is None:
            raise AssertionError(
                f"For the given action type `{action_type}`, the expected key for the payload (`{payload_key}`) is not found.",
                f"Available keys: {list(values.keys())}",
            )

        # Parse the payload into the correct instance if necessary
        parsed_payload = (
            payload
            if isinstance(payload, SimBotPayload)
            else action_type.payload_model.parse_obj(payload)
        )

        values["type"] = action_type

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
