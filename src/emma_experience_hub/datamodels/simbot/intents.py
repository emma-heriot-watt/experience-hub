from enum import Enum

from pydantic import BaseModel


class SimBotIntentType(Enum):
    """Different types of intents that can be extracted."""

    act = "act"
    clarify = "clarify"
    profanity = "profanity"


class SimBotIntent(BaseModel):
    """Model represenating the intent behind the utterance."""

    type: SimBotIntentType
