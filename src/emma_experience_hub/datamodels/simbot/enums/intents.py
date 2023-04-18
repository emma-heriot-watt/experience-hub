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

    # Improper instructions
    low_asr_confidence = "<language><low_asr_confidence>"
    profanity = "<language><profanity>"
    out_of_domain = "<language><out_of_domain>"
    only_wake_word = "<language><only_wake_word>"
    empty_utterance = "<language><empty_utterance>"

    # Clarification question triggers
    act_no_match = "<act><no_match>"
    act_too_many_matches = "<act><too_many_matches>"
    act_missing_inventory = "<act><missing_inventory>"

    # Confirmation question triggers
    confirm_generic = "<confirm><generic>"
    confirm_before_act = "<confirm><act>"
    confirm_before_goto_object = "<confirm><goto_object>"
    confirm_before_goto_viewpoint = "<confirm><goto_viewpoint>"
    confirm_before_search = "<confirm><search>"
    confirm_before_plan = "<confirm><plan>"

    # Question responses from the user
    clarify_answer = "<clarify><answer>"
    confirm_yes = "<confirm><yes>"
    confirm_no = "<confirm><no>"

    # Utterances that require only verbal responses
    ask_about_game = "<ask><about_game>"
    ask_about_agent = "<ask><about_agent>"
    ask_not_enough_information = "<not_enough_information>"
    ask_about_affordance = "<ask><about_affordance>"
    ask_about_appearance = "<ask><about_appearance>"
    ask_about_location = "<ask><about_location>"
    greeting = "<greeting>"
    admiration = "<admiration>"
    incomplete_utterance_find = "<incomplete_utterance_find>"
    incomplete_utterance_goto = "<incomplete_utterance_goto>"
    incomplete_utterance_pick = "<incomplete_utterance_pick>"

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
    def is_user_qa(self) -> bool:
        """Return True if the intent is one of the QA types."""
        return self.is_user_qa_type(self)

    @property
    def is_user_qa_about_object(self) -> bool:
        """Return True if the user is asking about an object."""
        return self in {
            SimBotIntentType.ask_about_affordance,
            SimBotIntentType.ask_about_appearance,
            SimBotIntentType.ask_about_location,
        }

    @property
    def is_actionable(self) -> bool:
        """Return True if the intent is a type of instruction."""
        return self.is_physical_interaction_intent_type(self)

    @property
    def triggers_question_to_user(self) -> bool:
        """Return True if the intent triggers a question to the user."""
        return self.triggers_confirmation_question or self.triggers_disambiguation_question

    @property
    def triggers_disambiguation_question(self) -> bool:
        """Did the agent ask for disambiguation from the user?"""
        return self == SimBotIntentType.act_too_many_matches

    @property
    def triggers_confirmation_question(self) -> bool:
        """Did the agent ask for confirmation from the user?"""
        return self in {
            SimBotIntentType.confirm_generic,
            SimBotIntentType.confirm_before_act,
            SimBotIntentType.confirm_before_goto_object,
            SimBotIntentType.confirm_before_goto_viewpoint,
            SimBotIntentType.confirm_before_search,
            SimBotIntentType.confirm_before_plan,
        }

    @property
    def is_confirmation_response(self) -> bool:
        """Return True if the intent is a response to a confirmation question."""
        return self in {
            SimBotIntentType.confirm_yes,
            SimBotIntentType.confirm_no,
        }

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
    ) -> TypeGuard[SimBotInvalidUtteranceIntentType]:
        """Return True if the intent type matches `SimBotInvalidUtteranceIntentType`."""
        return intent_type in SimBotInvalidUtteranceIntentType.__args__  # type: ignore[attr-defined]

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

    @staticmethod
    def is_user_qa_type(  # noqa: WPS602
        intent_type: SimBotIntentType,
    ) -> TypeGuard[SimBotUserQAType]:
        """Return True if the intent type matches `SimBotUserQAType`."""
        return intent_type in SimBotUserQAType.__args__  # type: ignore[attr-defined]


SimBotInvalidUtteranceIntentType = Literal[
    SimBotIntentType.low_asr_confidence,
    SimBotIntentType.out_of_domain,
    SimBotIntentType.profanity,
    SimBotIntentType.only_wake_word,
    SimBotIntentType.empty_utterance,
]

SimBotUserQAType = Literal[
    SimBotIntentType.ask_about_game,
    SimBotIntentType.ask_about_agent,
    SimBotIntentType.ask_about_affordance,
    SimBotIntentType.ask_about_location,
    SimBotIntentType.ask_about_appearance,
    SimBotIntentType.ask_not_enough_information,
    SimBotIntentType.greeting,
    SimBotIntentType.admiration,
    SimBotIntentType.incomplete_utterance_find,
    SimBotIntentType.incomplete_utterance_goto,
    SimBotIntentType.incomplete_utterance_pick,
]


SimBotUserIntentType = Literal[
    SimBotIntentType.clarify_answer,
    SimBotIntentType.confirm_yes,
    SimBotIntentType.confirm_no,
    SimBotIntentType.act,
    SimBotUserQAType,
]


SimBotAnyUserIntentType = Literal[
    SimBotUserIntentType,
    SimBotInvalidUtteranceIntentType,
    SimBotUserQAType,
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
    SimBotIntentType.confirm_generic,
    SimBotIntentType.confirm_before_act,
    SimBotIntentType.confirm_before_goto_object,
    SimBotIntentType.confirm_before_goto_viewpoint,
    SimBotIntentType.confirm_before_search,
    SimBotIntentType.confirm_before_plan,
    SimBotIntentType.act_no_match,
    SimBotIntentType.act_too_many_matches,
    SimBotIntentType.act_missing_inventory,
    SimBotIntentType.generic_success,
    SimBotIntentType.ask_about_affordance,
    SimBotIntentType.ask_about_location,
    SimBotIntentType.ask_about_appearance,
]

SimBotNLUIntentType = Literal[
    SimBotIntentType.act_no_match,
    SimBotIntentType.act_missing_inventory,
    SimBotIntentType.act_too_many_matches,
    SimBotIntentType.search,
    SimBotIntentType.act_one_match,
]
