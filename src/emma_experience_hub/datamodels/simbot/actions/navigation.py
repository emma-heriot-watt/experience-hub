from typing import Any, Literal, Union

from pydantic import BaseModel, Field, PositiveFloat, validator

from emma_experience_hub.datamodels.simbot.actions.object_interaction import (
    SimBotObjectInteractionObjectAction,
)


class SimBotGotoObjectAction(SimBotObjectInteractionObjectAction):
    """SimBot action for going to an object."""


class SimBotGotoRoomAction(BaseModel):
    """SimBot action for going to a room."""

    office_room: str = Field(..., alias="officeRoom")


class SimBotGotoViewpointAction(BaseModel):
    """SimBot action for navigating to a specific viewpoint."""

    go_to_point: str = Field(..., alias="goToPoint")


class SimBotGotoAction(BaseModel):
    """SimBot Goto action."""

    object: Union[SimBotGotoObjectAction, SimBotGotoRoomAction, SimBotGotoViewpointAction]


class SimBotLowLevelNavigationAction(BaseModel):
    """Base class for SimBot low-level navigation actions."""

    direction: Literal["Forward", "Backward", "Left", "Right", "Up", "Down", "Around"]
    magnitude: PositiveFloat


class SimbotMoveAction(SimBotLowLevelNavigationAction):
    """SimBot action for walking forwards or backwards."""

    direction: Literal["Forward", "Backward"]
    magnitude: PositiveFloat


class SimBotRotateAction(SimBotLowLevelNavigationAction):
    """SimBot action for rotating on the spot (changing heading)."""

    direction: Literal["Right", "Left"]
    magnitude: PositiveFloat = Field(min=0, max=359.0, help="Rotation degrees")  # noqa: WPS432


class SimBotLookAction(SimBotLowLevelNavigationAction):
    """SimBot action for looking up and down and around.

    For the around action, magnitude should always be set to 100.0. It returns four color images
    with slight edge overlap.
    """

    direction: Literal["Up", "Down", "Around"]
    magnitude: PositiveFloat = Field(min=0, max=100, help="Rotation degrees")

    @classmethod
    def create_look_around(cls) -> "SimBotLookAction":
        """Create a look around action."""
        return cls(direction="Around", magnitude=100)

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
