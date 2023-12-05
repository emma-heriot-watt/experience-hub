from enum import Enum

from pydantic import BaseModel


class Position(BaseModel):
    """3D position of an entity/location."""

    x: float
    y: float
    z: float

    def as_list(self) -> list[float]:
        """Return the coordinates as a list."""
        return [self.x, self.y, self.z]


class Rotation(BaseModel):
    """Rotation of an entity."""

    x: float
    y: float
    z: float

    def as_list(self) -> list[float]:
        """Return the coordinates as a list."""
        return [self.x, self.y, self.z]


class RotationQuaternion(Rotation):
    """Rotation quaternion of an entity."""

    w: float

    def as_list(self) -> list[float]:
        """Return the coordinates as a list."""
        return [self.x, self.y, self.z, self.w]


class ArenaLocation(BaseModel):
    """Exact location within arena."""

    room_name: str
    position: Position
    rotation: RotationQuaternion


class GFHLocationType(Enum):
    """The type of location used for GFH during the find routine."""

    viewpoint = "viewpoint"
    location = "location"
