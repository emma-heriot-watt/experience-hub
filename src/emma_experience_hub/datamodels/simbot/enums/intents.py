from __future__ import annotations

from enum import Enum
from typing import Literal

from typing_extensions import TypeGuard


class SimBotIntentType(Enum):
    """Different types of intents that can be extracted."""

    # Actionable
    act = "<act>"
    act_one_match = "<act><one_match>"
    search = "<search>"
    act_previous = "<act><previous>"

    # Clarification question triggers
    act_no_match = "<act><no_match>"
    act_too_many_matches = "<act><too_many_matches>"
    act_missing_inventory = "<act><missing_inventory>"

    clarify_answer = "<clarify><answer>"

    # Feedback for previous turn success
    generic_success = "<success><generic>"

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
    incorrect_action_format = "<failure><incorrect_action_format>"
    invalid_object_class = "<failure><invalid_object_class>"
    post_process_error = "<failure><post_process_error>"
    blocked_by_previous_error = "<failure><blocked_by_previous_error>"

    @property
    def is_invalid_user_utterance(self) -> bool:
        """Return True if the intent should not be used when generating an action."""
        return self.is_invalid_utterance_intent_type(self)

    @property
    def is_user_held_intent(self) -> bool:
        """Return True if the intent can be held by a user."""
        return self.is_user_intent_type(self)

    @property
    def is_environment_error(self) -> bool:
        """Return True if the intent is one of the Arena error types."""
        return self.is_environment_intent_type(self)

    @property
    def is_actionable(self) -> bool:
        """Return True if the intent is a type of instruction."""
        return self.is_physical_interaction_intent_type(self)

    @property
    def triggers_question_to_user(self) -> bool:
        """Return True if the intent triggers a question to the user."""
        return self.triggers_disambiguation_question

    @property
    def triggers_disambiguation_question(self) -> bool:
        """Did the agent ask for disambiguation from the user?"""
        return self == SimBotIntentType.act_too_many_matches

    @property
    def verbal_interaction_intent_triggers_search(self) -> bool:
        """Return True if the intent is a verbal interaction intent that triggers search."""
        return self in {
            SimBotIntentType.act_missing_inventory,
            SimBotIntentType.act_no_match,
        }

    @staticmethod
    def is_invalid_utterance_intent_type(  # noqa: WPS602
        intent_type: SimBotIntentType,
    ) -> bool:
        """Assume user utterances are always valid."""
        return False

    @staticmethod
    def is_user_intent_type(  # noqa: WPS602
        intent_type: SimBotIntentType,
    ) -> TypeGuard[SimBotUserIntentType]:
        """Return True if the intent type matches `SimBotUserIntentType`."""
        return intent_type in SimBotUserIntentType.__args__  # type: ignore[attr-defined]

    @staticmethod
    def is_environment_intent_type(  # noqa: WPS602
        intent_type: SimBotIntentType,
    ) -> TypeGuard[SimBotEnvironmentIntentType]:
        """Return True if the intent type matches `SimBotEnvironmentIntentType`."""
        return intent_type in SimBotEnvironmentIntentType.__args__  # type: ignore[attr-defined]

    @staticmethod
    def is_physical_interaction_intent_type(  # noqa: WPS602
        intent_type: SimBotIntentType,
    ) -> TypeGuard[SimBotPhysicalInteractionIntentType]:
        """Return True if the intent type matches `SimBotPhysicalInteractionIntentType`."""
        return intent_type in SimBotPhysicalInteractionIntentType.__args__  # type: ignore[attr-defined]

    @staticmethod
    def is_verbal_interaction_intent_type(  # noqa: WPS602
        intent_type: SimBotIntentType,
    ) -> TypeGuard[SimBotVerbalInteractionIntentType]:
        """Return True if the intent type matches `SimBotVerbalInteractionIntentType`."""
        return intent_type in SimBotVerbalInteractionIntentType.__args__  # type: ignore[attr-defined]


SimBotUserIntentType = Literal[
    SimBotIntentType.clarify_answer,
    SimBotIntentType.act,
]


SimBotEnvironmentIntentType = Literal[
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
    SimBotIntentType.incorrect_action_format,
    SimBotIntentType.invalid_object_class,
    SimBotIntentType.post_process_error,
    SimBotIntentType.blocked_by_previous_error,
]

SimBotPhysicalInteractionIntentType = Literal[
    SimBotIntentType.act,
    SimBotIntentType.act_one_match,
    SimBotIntentType.search,
    SimBotIntentType.act_previous,
]

SimBotVerbalInteractionIntentType = Literal[
    SimBotIntentType.act_no_match,
    SimBotIntentType.act_too_many_matches,
    SimBotIntentType.act_missing_inventory,
    SimBotIntentType.generic_success,
]

SimBotCRIntentType = Literal[
    SimBotIntentType.act_no_match,
    SimBotIntentType.act_missing_inventory,
    SimBotIntentType.act_too_many_matches,
    SimBotIntentType.search,
    SimBotIntentType.act_one_match,
]
