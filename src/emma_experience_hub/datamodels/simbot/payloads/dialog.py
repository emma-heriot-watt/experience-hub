from pydantic import Field

from emma_experience_hub.datamodels.simbot.payloads.payload import SimBotPayload


class SimBotDialogPayload(SimBotPayload):
    """Dialog action for the SimBot arena.

    Returning this action will also dicate a ''stop action'' to Arena Runtime system.
    """

    value: str  # noqa: WPS110
    rule_id: int = Field(..., description="the id of the rule used to generate the response")
