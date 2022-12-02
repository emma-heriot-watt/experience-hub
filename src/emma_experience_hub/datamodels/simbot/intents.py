from typing import Optional

from pydantic import BaseModel

from emma_experience_hub.datamodels.simbot.enums import SimBotActionType, SimBotIntentType


class SimBotIntent(BaseModel):
    """Model represenating the intent behind the utterance."""

    type: SimBotIntentType
    action: Optional[SimBotActionType] = None
    entity: Optional[str] = None
