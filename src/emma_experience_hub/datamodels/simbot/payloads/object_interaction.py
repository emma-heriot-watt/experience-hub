from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from emma_experience_hub.datamodels.simbot.payloads.payload import SimBotPayload


SimBotObjectMaskType = list[list[int]]


class SimBotObjectOutputType(Enum):
    """Different object output types supported by the SimBot arena."""

    object_class = "OBJECT_CLASS"
    object_mask = "OBJECT_MASK"

    @classmethod
    def default(cls) -> "SimBotObjectOutputType":
        """Get the default type."""
        return SimBotObjectOutputType.object_mask

    @classmethod
    def get_type_from_args(cls, name: Optional[str]) -> "SimBotObjectOutputType":
        """Automatically return the correct type given the parameters."""
        # Manual override if stickynote
        if name is not None and "sticky" in name.lower():
            return SimBotObjectOutputType.object_class

        # Otherwise return mask
        return SimBotObjectOutputType.default()


class SimBotInteractionObject(BaseModel):
    """SimBot object interaction action."""

    color_image_index: int = Field(0, alias="colorImageIndex")
    mask: Optional[SimBotObjectMaskType] = None
    name: str

    @property
    def object_output_type(self) -> SimBotObjectOutputType:
        """Get the correct object output type from the given args."""
        return SimBotObjectOutputType.get_type_from_args(self.name)

    @property
    def entity_name(self) -> str:
        """Get the name of the entity."""
        return self.name


class SimBotObjectInteractionPayload(SimBotPayload):
    """SimBot object interaction action, within the correct wrapping."""

    object: SimBotInteractionObject

    @property
    def entity_name(self) -> str:
        """Get the name of the entity."""
        return self.object.name
