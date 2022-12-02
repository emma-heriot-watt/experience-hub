from emma_experience_hub.datamodels.simbot.enums.intents import SimBotIntentType
from emma_experience_hub.datamodels.simbot.payloads.payload import SimBotPayload


class SimBotDialogPayload(SimBotPayload):
    """Dialog action for the SimBot arena.

    Returning this action will also dicate a ''stop action'' to Arena Runtime system.
    """

    value: str  # noqa: WPS110
    intent: SimBotIntentType
