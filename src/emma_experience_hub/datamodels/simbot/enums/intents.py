from enum import Enum


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

    # Confirmation question triggers
    confirm_before_act = "<confirm><act>"
    confirm_generic = "<confirm><generic>"

    # Question responses from the user
    clarify_answer = "<clarify><answer>"
    confirm_yes = "<confirm><yes>"
    confirm_no = "<confirm><no>"

    # Feedback for search
    search_found_object = "<search><highlight>"
    search_not_found_object = "<search><not_found_object>"
    search_look_around = "<search><look_around>"
    search_goto_viewpoint = "<search><goto_viewpoint>"
    search_goto_room = "<search><goto_room>"

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
        return self in {
            SimBotIntentType.low_asr_confidence,
            SimBotIntentType.out_of_domain,
            SimBotIntentType.profanity,
            SimBotIntentType.only_wake_word,
            SimBotIntentType.empty_utterance,
        }

    @property
    def is_user_held_intent(self) -> bool:
        """Return True if the intent can be held by a user."""
        return self.is_invalid_user_utterance or self in {
            SimBotIntentType.clarify_answer,
            SimBotIntentType.confirm_yes,
            SimBotIntentType.confirm_no,
            SimBotIntentType.act,
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
            SimBotIntentType.incorrect_action_format,
            SimBotIntentType.invalid_object_class,
            SimBotIntentType.post_process_error,
            SimBotIntentType.blocked_by_previous_error,
        }

    @property
    def triggers_question_to_user(self) -> bool:
        """Return True if the intent triggers a question to the user."""
        return (
            self.is_clarification_question
            or self.triggers_confirmation_question
            or self.triggers_disambiguation_question
        )

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
        }

    @property
    def is_clarification_question(self) -> bool:
        """Return True if intent is one that triggers a clarification question."""
        return self in {
            SimBotIntentType.act_no_match,
            SimBotIntentType.act_too_many_matches,
        }

    @property
    def is_confirmation_response(self) -> bool:
        """Return True if the intent is a response to a confirmation question."""
        return self in {
            SimBotIntentType.confirm_yes,
            SimBotIntentType.confirm_no,
        }

    @property
    def is_actionable(self) -> bool:
        """Return True if the intent is a type of instruction."""
        return self in {
            SimBotIntentType.act,
            SimBotIntentType.act_one_match,
            SimBotIntentType.search,
            SimBotIntentType.act_previous,
        }

    @property
    def is_search_feedback(self) -> bool:
        """Return True if the intent is used for providing feedback during search sub-routine."""
        return self in {
            SimBotIntentType.search_not_found_object,
            SimBotIntentType.search_look_around,
            SimBotIntentType.search_goto_viewpoint,
            SimBotIntentType.search_goto_room,
        }
