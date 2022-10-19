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
    def get_type_from_args(
        cls, mask: Optional[SimBotObjectMaskType], name: Optional[str]
    ) -> "SimBotObjectOutputType":
        """Automatically return the correct type given the parameters."""
        # Manual override if stickynote
        if name is not None and "sticky" in name.lower():
            return SimBotObjectOutputType.object_class

        if mask is not None:
            return SimBotObjectOutputType.object_mask

        if name is not None:
            return SimBotObjectOutputType.object_class

        raise AssertionError(
            "Unable to automatically get the object output type from the arguments the combination is not supported."
        )


class SimBotInteractionObject(BaseModel):
    """SimBot object interaction action."""

    color_image_index: int = Field(0, alias="colorImageIndex")
    mask: Optional[SimBotObjectMaskType] = None
    name: str

    @property
    def object_output_type(self) -> SimBotObjectOutputType:
        """Get the correct object output type from the given args."""
        return SimBotObjectOutputType.get_type_from_args(self.mask, self.name)


class SimBotObjectInteractionPayload(SimBotPayload):
    """SimBot object interaction action, within the correct wrapping."""

    object: SimBotInteractionObject
