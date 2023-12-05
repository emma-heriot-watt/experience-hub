import pytest
from hypothesis import given
from pytest_cases import fixture, parametrize

from emma_experience_hub.datamodels.simbot.actions import SimBotAction, SimBotActionType
from emma_experience_hub.datamodels.simbot.payloads import SimBotObjectOutputType, SimBotPayload
from tests.fixtures.simbot_actions import simbot_actions


@fixture(scope="module")
def action_type_to_payload_model_switcher() -> dict[str, type[SimBotPayload]]:
    return SimBotActionType.action_type_to_payload_model()


@parametrize("action_type", list(SimBotActionType))
def test_action_type_has_payload_model_mapping(
    action_type: SimBotActionType,
    action_type_to_payload_model_switcher: dict[str, type[SimBotPayload]],
) -> None:
    """Verify that each action type maps to a pydantic model.

    This ensures that each action can be automatically parsed through the `SimBotAction`.
    """
    # Verify the action type exists as a key in the switcher dict
    assert action_type.name in action_type_to_payload_model_switcher

    # Verify that the action type has a payload
    model = action_type_to_payload_model_switcher[action_type.name]
    assert isinstance(model, type(SimBotPayload))


@given(simbot_actions())
def test_ensure_payload_field_is_not_exported_from_action(action: SimBotAction) -> None:
    assert action

    assert "payload" not in action.dict()


@given(simbot_actions())
def test_payload_field_automatically_converted_to_correct_attribute(action: SimBotAction) -> None:
    assert action

    # Get the correct key for the action type
    payload_key = action.type.base_type.value.strip()

    # Make sure that key exists
    assert getattr(action, payload_key)
    assert payload_key in action.dict()


@given(simbot_actions())
def test_object_output_type_is_mask_for_all_action_types_except_examine(
    action: SimBotAction,
) -> None:
    assert action

    if action.type == SimBotActionType.Examine:
        assert action.object_output_type != SimBotObjectOutputType.object_mask
    else:
        assert action.object_output_type == SimBotObjectOutputType.object_mask


@pytest.mark.skip(reason="not implemented")
def test_action_can_be_instantiated_without_given_payload_field() -> None:
    raise NotImplementedError
