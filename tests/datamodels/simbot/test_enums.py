from emma_experience_hub.datamodels.simbot.enums import SimBotActionStatusType, SimBotIntentType


def test_ensure_arena_error_types_are_in_intents() -> None:
    """We need to make sure that all arena error types are included in the intents."""
    ignored_statuses = {SimBotActionStatusType.action_successful}

    for action_status_type in SimBotActionStatusType:
        if action_status_type in ignored_statuses:
            continue

        # The actiopn status should be able to be converted to an intent type
        status_as_intent_type = SimBotIntentType[action_status_type.name]

        assert status_as_intent_type
        assert status_as_intent_type.is_environment_error
