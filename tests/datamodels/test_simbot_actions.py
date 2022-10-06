from pydantic import BaseModel

from emma_experience_hub.datamodels.simbot.actions import SimBotActionType


def test_each_action_type_has_model_mapping() -> None:
    """Verify that each action type maps to a pydantic model.

    This ensures that each action can be automatically parsed through the `SimBotAction`.
    """
    switcher = SimBotActionType.action_type_to_payload_model()
    for action_type in SimBotActionType:
        # Verify the action type exists as a key
        assert action_type.name in switcher

        # Verify that the model exists
        model = switcher[action_type.name]
        assert isinstance(model, type(BaseModel))
