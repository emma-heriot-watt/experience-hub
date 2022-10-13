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
    out_of_domain = "<out_of_domain>"
    low_asr_confidence = "<low_asr_confidence>"

    @property
    def is_clarification_question(self) -> bool:
        """Return True if intent is one that triggers a clarification question."""
        return self in {
            SimBotIntentType.clarify_direction,
            SimBotIntentType.clarify_description,
            SimBotIntentType.clarify_location,
            SimBotIntentType.clarify_disambiguation,
        }


class SimBotIntent(BaseModel):
    """Model represenating the intent behind the utterance."""

    type: SimBotIntentType
    object_name: Optional[str] = None
