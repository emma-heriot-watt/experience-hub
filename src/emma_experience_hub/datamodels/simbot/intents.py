from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SimBotIntentType(Enum):
    """Different types of intents that can be extracted."""

    instruction = "<act>"
    clarify_direction = "<clarify><direction>"
    clarify_description = "<clarify><decription>"
    clarify_location = "<clarify><location>"
    clarify_disambiguation = "<clarify><disambiguation>"
    clarify_question = "<clarify><question>"
    clarify_answer = "<clarify><answer>"
    profanity = "<profanity>"
    end_of_trajectory = "<end_of_trajectory>"


class SimBotIntent(BaseModel):
    """Model represenating the intent behind the utterance."""

    type: SimBotIntentType
    object_name: Optional[str] = None
