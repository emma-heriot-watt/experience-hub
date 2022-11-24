from enum import Enum
from typing import Optional

from pydantic import BaseModel

from emma_experience_hub.datamodels.simbot.actions import SimBotActionType


class SimBotIntentType(Enum):
    """Different types of intents that can be extracted."""

    # Actionable
    act = "<act>"
    act_low_level = "<act><low_level>"
    act_search = "<act><search>"
    act_previous = "<act><previous>"
    press_button = "<act><press_button>"

    # Improper instructions
    low_asr_confidence = "<language><low_asr_confidence>"
    profanity = "<language><profanity>"
    out_of_domain = "<language><out_of_domain>"
    only_wake_word = "<language><only_wake_word>"
    empty_utterance = "<language><empty_utterance>"

    # Clarification questions
    clarify_direction = "<clarify><direction>"
    clarify_description = "<clarify><description>"
    clarify_location = "<clarify><location>"
    clarify_disambiguation = "<clarify><disambiguation>"
    clarify_confirmation = "<clarify><confirmation>"

    # Clarification answer from the user
    clarify_answer = "<clarify><answer>"

    # Feedback for success
    generic_success = "<success><generic>"
    object_interaction_success = "<success><object_interaction>"
    low_level_navigation_success = "<success><low_level_navigation>"
    goto_room_success = "<success><goto_room>"
    goto_object_success = "<success><goto_object>"

    # Feedback for failure
    generic_failure = "<failure><generic>"

    # Arena error failures
    unsupported_action = "<failure><unsupported_action>"
    unsupported_navigation = "<failure><unsupported_navigation>"
    already_holding_object = "<failure><already_holding_object>"
    receptacle_is_full = "<failure><receptacle_is_full>"
    receptacle_is_closed = "<failure><receptacle_is_closed>"
    target_inaccessible = "<failure><target_inaccessible>"
    killed_by_hazard = "<failure><killed_by_hazard>"
    target_out_of_range = "<failure><target_out_of_range>"
    alternate_navigation_used = "<failure><alternate_navigation_used>"
    object_overloaded = "<failure><object_overloaded>"
    object_unpowered = "<failure><object_unpowered>"
    invalid_command = "<failure><invalid_command>"
    object_not_picked_up = "<failure><object_not_picked_up>"
    arena_unavailable = "<failure><arena_unavailable>"
    action_execution_error = "<failure><action_execution_error>"

    @property
    def is_invalid_user_utterance(self) -> bool:
        """Return True if the intent should not be used when generating an action."""
        return self in {
            SimBotIntentType.low_asr_confidence,
            SimBotIntentType.out_of_domain,
            SimBotIntentType.press_button,
            SimBotIntentType.profanity,
            SimBotIntentType.only_wake_word,
            SimBotIntentType.empty_utterance,
        }

    @property
    def is_user_held_intent(self) -> bool:
        """Return True if the intent can be held by a user."""
        return self.is_invalid_user_utterance or self in {
            SimBotIntentType.clarify_answer,
            SimBotIntentType.act,
            SimBotIntentType.press_button,
        }

    @property
    def is_environment_error(self) -> bool:
        """Return True if the intent is one of the Arena error types."""
        return self in {
            SimBotIntentType.unsupported_action,
            SimBotIntentType.unsupported_navigation,
            SimBotIntentType.already_holding_object,
            SimBotIntentType.receptacle_is_full,
            SimBotIntentType.receptacle_is_closed,
            SimBotIntentType.target_inaccessible,
            SimBotIntentType.killed_by_hazard,
            SimBotIntentType.target_out_of_range,
            SimBotIntentType.alternate_navigation_used,
            SimBotIntentType.object_overloaded,
            SimBotIntentType.object_unpowered,
            SimBotIntentType.invalid_command,
            SimBotIntentType.object_not_picked_up,
            SimBotIntentType.arena_unavailable,
            SimBotIntentType.action_execution_error,
        }

    @property
    def is_clarification_question(self) -> bool:
        """Return True if intent is one that triggers a clarification question."""
        return self in {
            SimBotIntentType.clarify_direction,
            SimBotIntentType.clarify_description,
            SimBotIntentType.clarify_location,
            SimBotIntentType.clarify_disambiguation,
            SimBotIntentType.clarify_confirmation,
        }

    @property
    def is_actionable(self) -> bool:
        """Return True if the intent is a type of instruction."""
        return self in {
            SimBotIntentType.act,
            SimBotIntentType.act_low_level,
            SimBotIntentType.act_search,
            SimBotIntentType.act_previous,
            SimBotIntentType.press_button,
        }


class SimBotIntent(BaseModel):
    """Model represenating the intent behind the utterance."""

    type: SimBotIntentType
    action: Optional[SimBotActionType] = None
    entity: Optional[str] = None
