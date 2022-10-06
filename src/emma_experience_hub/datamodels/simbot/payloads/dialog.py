from typing import Optional

from emma_experience_hub.datamodels.simbot.intents import SimBotIntentType
from emma_experience_hub.datamodels.simbot.payloads.payload import SimBotPayload


class SimBotDialogPayload(SimBotPayload):
    """Dialog action for the SimBot arena.

    Returning this action will also dicate a ''stop action'' to Arena Runtime system.
    """

    value: str  # noqa: WPS110
    intent: Optional[SimBotIntentType] = None
