from typing import Any, Literal, Optional, Union

from pydantic import Field, NonNegativeFloat, PositiveFloat, validator

from emma_experience_hub.datamodels.common import Position, RotationQuaternion
from emma_experience_hub.datamodels.simbot.payloads.object_interaction import (
    SimBotInteractionObject,
)
from emma_experience_hub.datamodels.simbot.payloads.payload import SimBotPayload


class SimBotGotoObject(SimBotInteractionObject):
    """SimBot action for going to an object."""


class SimBotGotoRoom(SimBotPayload):
    """SimBot action for going to a room."""

    office_room: str = Field(..., alias="officeRoom")

    @property
    def entity_name(self) -> str:
        """Get the name of the entity."""
        return self.office_room


class SimBotGotoViewpoint(SimBotPayload):
    """SimBot action for navigating to a specific viewpoint."""

    go_to_point: str = Field(..., alias="goToPoint")

    @property
    def entity_name(self) -> Optional[str]:
        """Get the name of the entity."""
        return self.go_to_point


class SimBotGotoPosition(SimBotPayload):
    """SimBot action for going to an object."""

    position: Position
    rotation: RotationQuaternion


class SimBotGotoPayload(SimBotPayload, smart_union=True):
    """SimBot Goto action."""

    object: Union[SimBotGotoObject, SimBotGotoRoom, SimBotGotoViewpoint, SimBotGotoPosition]

    @property
    def entity_name(self) -> Optional[str]:
        """Get the name of the entity."""
        return self.object.entity_name


class SimBotGotoRoomPayload(SimBotGotoPayload):
    """SimBot Goto room action."""

    object: SimBotGotoRoom


class SimBotGotoViewpointPayload(SimBotGotoPayload):
    """SimBot Goto viewpoint action."""

    object: SimBotGotoViewpoint


class SimBotGotoObjectPayload(SimBotGotoPayload):
    """SimBot Goto object action."""

    object: SimBotGotoObject


class SimBotGotoPositionPayload(SimBotGotoPayload):
    """SimBot Goto object action."""

    object: SimBotGotoPosition


class SimBotNavigationPayload(SimBotPayload):
    """Base class for SimBot low-level navigation actions."""

    direction: Literal["Forward", "Backward", "Left", "Right", "Up", "Down", "Around"]
    magnitude: PositiveFloat


class SimBotMovePayload(SimBotNavigationPayload):
    """SimBot action for walking forwards or backwards."""

    direction: Literal["Forward", "Backward"]
    magnitude: NonNegativeFloat = 1


class SimBotMoveForwardPayload(SimBotMovePayload):
    """SimBot action for moving forwards."""

    direction: Literal["Forward"] = "Forward"


class SimBotMoveBackwardPayload(SimBotMovePayload):
    """SimBot action for moving backwards."""

    direction: Literal["Backward"] = "Backward"


class SimBotRotatePayload(SimBotNavigationPayload):
    """SimBot action for rotating on the spot (changing heading)."""

    direction: Literal["Right", "Left"]
    magnitude: PositiveFloat = Field(min=0, max=359.0, help="Rotation degrees")  # noqa: WPS432


class SimBotRotateLeftPayload(SimBotRotatePayload):
    """SimBot action for rotating left.

    Defaults to 45deg turn.
    """

    direction: Literal["Left"] = "Left"
    magnitude: PositiveFloat = 45


class SimBotTurnAroundPayload(SimBotRotateLeftPayload):
    """SimBot action for turning around.

    Defaults to 180deg turn.
    """

    direction: Literal["Left"] = "Left"
    magnitude: PositiveFloat = 180


class SimBotRotateRightPayload(SimBotRotatePayload):
    """SimBot action for rotating right.

    Defaults to 45deg turn.
    """

    direction: Literal["Right"] = "Right"
    magnitude: PositiveFloat = 45


class SimBotLookPayload(SimBotNavigationPayload):
    """SimBot action for looking up and down and around.

    For the around action, magnitude should always be set to 100.0. It returns four color images
    with slight edge overlap.
    """

    direction: Literal["Up", "Down", "Around"]
    magnitude: PositiveFloat = Field(min=0, max=100, help="Rotation degrees")

    @validator("magnitude")
    @classmethod
    def validate_magitude_for_direction(
        cls,
        magnitude: float,
        values: dict[str, Any],  # noqa: WPS110
    ) -> float:
        """Validate magnitude value for the given direction."""
        direction = values.get("direction", None)
        if not direction:
            raise AssertionError("There should be a direction?")

        if direction != "Around" and 0 <= magnitude <= 60:
            return magnitude

        if direction == "Around":
            return magnitude

        raise AssertionError("Magnitude is not valid. It should be within (0,60) for up/down.")


class SimBotLookUpPayload(SimBotLookPayload):
    """SimBot payload for looking up.

    Default to 30 degrees.
    """

    direction: Literal["Up"] = "Up"
    magnitude: PositiveFloat = 30


class SimBotLookDownPayload(SimBotLookPayload):
    """SimBot payload for looking down.

    Default to 30 degrees.
    """

    direction: Literal["Down"] = "Down"
    magnitude: PositiveFloat = 30


class SimBotLookAroundPayload(SimBotLookPayload):
    """SimBot payload for looking around.

    Default to 100 degrees field of view
    """

    direction: Literal["Around"] = "Around"
    magnitude: PositiveFloat = 100
