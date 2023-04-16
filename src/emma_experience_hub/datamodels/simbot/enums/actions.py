from enum import Enum

from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN, PREDICTED_ACTION_DELIMITER
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotAuxiliaryMetadataPayload,
    SimBotDialogPayload,
    SimBotGotoObjectPayload,
    SimBotGotoPayload,
    SimBotGotoPositionPayload,
    SimBotGotoRoomPayload,
    SimBotGotoViewpointPayload,
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
    GotoRoom = "goto room"  # noqa: WPS115
    GotoObject = "goto object"  # noqa: WPS115
    GotoPosition = "goto position"  # noqa: WPS115
    GotoViewpoint = "goto viewpoint"  # noqa: WPS115

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
    Highlight = "highlight"  # noqa: WPS115
    # Burn = "burn"
    # Slice = "slice"
    # Throw = "throw"
    # Use = "use"

    # Language
    Dialog = "dialog"  # noqa: WPS115
    LightweightDialog = "lightweightDialog"  # noqa: WPS115
    SpeechRecognition = "recognition"  # noqa: WPS115

    # Other
    GameMetaData = "metaData"  # noqa: WPS115

    @classmethod
    def sensors(cls) -> list["SimBotActionType"]:
        """Action types which are recieved from the environment."""
        return [SimBotActionType.SpeechRecognition, SimBotActionType.GameMetaData]

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
            SimBotActionType.GotoRoom,
            SimBotActionType.GotoObject,
            SimBotActionType.GotoPosition,
            SimBotActionType.GotoViewpoint,
        ]

    @classmethod
    def low_level_navigation(cls) -> list["SimBotActionType"]:
        """Get all the low-level navigation action types.

        All of these have pre-instantiated payloads too.
        """
        return [
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
            SimBotActionType.Highlight,
        ]

    @classmethod
    def language(cls) -> list["SimBotActionType"]:
        """Get all language action types from the SimBot Arena."""
        return [
            SimBotActionType.Dialog,
            SimBotActionType.LightweightDialog,
            SimBotActionType.SpeechRecognition,
        ]

    @classmethod
    def action_type_to_payload_model(cls) -> dict[str, type[SimBotPayload]]:
        """Get a map from each action type to the payload model."""
        switcher: dict[str, type[SimBotPayload]] = {
            # Sensors
            "SpeechRecognition": SimBotSpeechRecognitionPayload,
            "GameMetaData": SimBotAuxiliaryMetadataPayload,
            # Dialog
            "Dialog": SimBotDialogPayload,
            "LightweightDialog": SimBotDialogPayload,
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
            "GotoRoom": SimBotGotoRoomPayload,
            "GotoObject": SimBotGotoObjectPayload,
            "GotoViewpoint": SimBotGotoViewpointPayload,
            "GotoPosition": SimBotGotoPositionPayload,
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
            "Highlight": SimBotObjectInteractionPayload,
        }
        return switcher

    @classmethod
    def from_payload_model(cls, payload_model: SimBotPayload) -> "SimBotActionType":
        """Get the correct action type from the provided payload."""
        switcher = {
            payload_model: SimBotActionType[action_type_name]
            for action_type_name, payload_model in SimBotActionType.action_type_to_payload_model().items()
        }
        return switcher[type(payload_model)]

    @classmethod
    def base_type_to_aliases(cls) -> dict["SimBotActionType", set["SimBotActionType"]]:
        """Map each base type to its aliases."""
        return {
            SimBotActionType.Move: {
                SimBotActionType.MoveForward,
                SimBotActionType.MoveBackward,
            },
            SimBotActionType.Look: {
                SimBotActionType.LookAround,
                SimBotActionType.LookDown,
                SimBotActionType.LookUp,
            },
            SimBotActionType.Rotate: {
                SimBotActionType.RotateLeft,
                SimBotActionType.RotateRight,
                SimBotActionType.TurnAround,
            },
            SimBotActionType.Goto: {
                SimBotActionType.GotoObject,
                SimBotActionType.GotoRoom,
                SimBotActionType.GotoViewpoint,
                SimBotActionType.GotoPosition,
            },
        }

    @classmethod
    def alias_to_base_type(cls) -> dict["SimBotActionType", "SimBotActionType"]:
        """Map each alias to its base type."""
        return {
            alias_type: base_type
            for base_type, alias_types in cls.base_type_to_aliases().items()
            for alias_type in alias_types
        }

    @classmethod
    def move_aliases(cls) -> set["SimBotActionType"]:
        """Return all the move aliases."""
        return cls.base_type_to_aliases()[SimBotActionType.Move]

    @classmethod
    def look_aliases(cls) -> set["SimBotActionType"]:
        """Return all the look aliases."""
        return cls.base_type_to_aliases()[SimBotActionType.Look]

    @classmethod
    def rotate_aliases(cls) -> set["SimBotActionType"]:
        """Return all the rotate aliases."""
        return cls.base_type_to_aliases()[SimBotActionType.Rotate]

    @classmethod
    def goto_aliases(cls) -> set["SimBotActionType"]:
        """Return all the goto action aliases."""
        return cls.base_type_to_aliases()[SimBotActionType.Goto]

    @classmethod
    def base_types(cls) -> set["SimBotActionType"]:
        """Get all the actions with a base type."""
        return set(cls.base_type_to_aliases().keys())

    @property
    def base_type(self) -> "SimBotActionType":
        """Given a specific type, returns the base Simbot action type."""
        possible_base_type = self.alias_to_base_type().get(self)
        return possible_base_type if possible_base_type else self

    @property
    def has_base_type(self) -> bool:
        """Return True if the current action type has a base type."""
        return self.base_type != self

    @property
    def payload_model(self) -> type[SimBotPayload]:
        """Get the corresponding payload for the SimBot action type."""
        return self.action_type_to_payload_model()[self.name]


class SimBotDummyRawActions(Enum):
    """The raw output of all dummy actions in the SimBot Arena."""

    # Navigation
    DummyLookDown = (  # noqa: WPS115
        f"dummy look down {END_OF_TRAJECTORY_TOKEN}{PREDICTED_ACTION_DELIMITER}"
    )
