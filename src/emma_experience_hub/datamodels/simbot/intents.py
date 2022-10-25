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
    press_button = "<press_button>"

    @property
    def is_clarification_question(self) -> bool:
        """Return True if intent is one that triggers a clarification question."""
        return self in {
            SimBotIntentType.clarify_direction,
            SimBotIntentType.clarify_description,
            SimBotIntentType.clarify_location,
            SimBotIntentType.clarify_disambiguation,
            SimBotIntentType.clarify_question,
        }

    @property
    def is_instruction(self) -> bool:
        """Return True if the intent is a type of instruction."""
        return self in {SimBotIntentType.instruction, SimBotIntentType.press_button}

    @property
    def is_actionable(self) -> bool:
        """Return True if the intent is one we can act on.

        We can act on instructions and clarifcation QA's.
        """
        return (
            self is SimBotIntentType.clarify_answer
            or self.is_instruction
            or self.is_clarification_question
        )


class SimBotIntent(BaseModel):
    """Model represenating the intent behind the utterance."""

    type: SimBotIntentType
    object_name: Optional[str] = None
