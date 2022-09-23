from pydantic import BaseModel

from emma_experience_hub.datamodels.simbot.actions import (
    SIMBOT_ACTION_TYPE_TO_KEY_MAPPING,
    SimBotActionType,
    SimBotActionTypePayloadModelMap,
)


def test_each_action_type_has_key_mapping() -> None:
    """Verify that each action type maps to a key for the action.

    Because of how the dicts are constructed, we need to make sure that each action is accounted
    for and validated properly.
    """
    all_action_types = SimBotActionType.__args__

    for action_type in all_action_types:
        # Verify the action exists
        assert action_type in SIMBOT_ACTION_TYPE_TO_KEY_MAPPING

        # Verify that the mapped dict key exists
        dict_key = SIMBOT_ACTION_TYPE_TO_KEY_MAPPING[action_type]
        assert dict_key


def test_each_action_type_has_model_mapping() -> None:
    """Verify that each action type maps to a pydantic model.

    This ensures that each action can be automatically parsed through the `SimBotAction`.
    """
    all_action_types = SimBotActionType.__args__

    for action_type in all_action_types:
        # Verify the action type exists as a key
        assert action_type in SimBotActionTypePayloadModelMap

        # Verify that the model exists
        model = SimBotActionTypePayloadModelMap[action_type]
        assert isinstance(model, type(BaseModel))
