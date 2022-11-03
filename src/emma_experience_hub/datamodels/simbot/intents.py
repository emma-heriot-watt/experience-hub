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

    # Arena Error Types
    already_holding_object = "<feedback><negative><already_holding_object>"
    receptacle_is_full = "<feedback><negative><receptacle_is_full>"
    receptacle_is_closed = "<feedback><negative><receptacle_is_closed>"
    target_inaccessible = "<feedback><negative><target_inaccessible>"
    target_out_of_range = "<feedback><negative><target_out_of_range>"
    object_overloaded = "<feedback><negative><object_overloaded>"
    object_unpowered = "<feedback><negative><object_unpowered>"
    no_free_hand = "<feedback><negative><no_free_hand>"
    object_not_picked_up = "<feedback><negative><object_not_picked_up>"

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

    @property
    def is_arena_error(self) -> bool:
        """Return True if the Enum is one of the Arena error types."""
        return self in {
            SimBotIntentType.already_holding_object,
            SimBotIntentType.receptacle_is_full,
            SimBotIntentType.receptacle_is_closed,
            SimBotIntentType.target_inaccessible,
            SimBotIntentType.target_out_of_range,
            SimBotIntentType.object_overloaded,
            SimBotIntentType.object_unpowered,
            SimBotIntentType.no_free_hand,
            SimBotIntentType.object_not_picked_up,
        }


class SimBotIntent(BaseModel):
    """Model represenating the intent behind the utterance."""

    type: SimBotIntentType
    object_name: Optional[str] = None
