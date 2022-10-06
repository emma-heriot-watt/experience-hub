from typing import Optional

from pydantic import BaseModel, Field

from emma_experience_hub.datamodels.simbot.payloads.payload import SimBotPayload


class SimBotInteractionObject(BaseModel):
    """SimBot object interaction action."""

    color_image_index: int = Field(0, alias="colorImageIndex")
    mask: Optional[list[list[int]]] = None
    name: str


class SimBotObjectInteractionPayload(SimBotPayload):
    """SimBot object interaction action, within the correct wrapping."""

    object: SimBotInteractionObject
