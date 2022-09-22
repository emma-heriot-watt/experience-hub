from pydantic import BaseModel


class SimBotDialogAction(BaseModel):
    """Dialog action for the SimBot arena.

    Returning this action will also dicate a ''stop action'' to Arena Runtime system.
    """

    value: str  # noqa: WPS110
