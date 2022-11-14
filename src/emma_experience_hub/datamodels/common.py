from pydantic import BaseModel


class Position(BaseModel):
    """3D position of an entity/location."""

    x: float
    y: float
    z: float


class Rotation(BaseModel):
    """Rotation of an entity."""

    x: float
    y: float
    z: float


class RotationQuaternion(Rotation):
    """Rotation quaternion of an entity."""

    w: float
