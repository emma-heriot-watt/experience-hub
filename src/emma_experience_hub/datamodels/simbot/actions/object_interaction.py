from pydantic import BaseModel, Field


class SimBotObjectInteractionObjectAction(BaseModel):
    """SimBot object interaction action."""

    color_image_index: int = Field(0, alias="colorImageIndex")
    # TODO: What should the mask be?
    mask: str
    name: str


class SimBotObjectInteractionAction(BaseModel):
    """SimBot object interaction action, within the correct wrapping."""

    object: SimBotObjectInteractionObjectAction
