from hypothesis import given

from emma_experience_hub.datamodels.simbot.actions import SimBotAction
from emma_experience_hub.datamodels.simbot.session import SimBotSessionTurnActions
from tests.fixtures.simbot_actions import (
    simbot_actions,
    simbot_dialog_payloads,
    simbot_interaction_payloads,
)


@given(
    interaction_action=simbot_actions(simbot_interaction_payloads()),
    dialog_action=simbot_actions(simbot_dialog_payloads()),
)
def test_actions_always_have_correct_ids(
    interaction_action: SimBotAction, dialog_action: SimBotAction
) -> None:
    # Create empty turn action
    turn_actions = SimBotSessionTurnActions()
    assert not turn_actions.interaction
    assert not turn_actions.dialog

    # Add in interaction action and make sure it has an id of 0
    turn_actions.interaction = interaction_action
    assert turn_actions.interaction.id == 0

    # Add in a dialog action and make sure it has an id of 1
    turn_actions.dialog = dialog_action
    assert turn_actions.interaction.id == 0
    assert turn_actions.dialog.id == 1

    # Remove the interaction action and make sure the dialog action now has an id of 0
    turn_actions.interaction = None
    assert not turn_actions.interaction
    assert turn_actions.dialog.id == 0

    # Add the interaction action back and make sure the ids are correct
    turn_actions.interaction = interaction_action
    assert turn_actions.interaction.id == 0
    assert turn_actions.dialog.id == 1


@given(
    interaction_action=simbot_actions(simbot_interaction_payloads()),
    dialog_action=simbot_actions(simbot_dialog_payloads()),
)
def test_actions_as_list_are_in_correct_order(
    interaction_action: SimBotAction, dialog_action: SimBotAction
) -> None:
    # Create empty turn action
    turn_actions = SimBotSessionTurnActions()
    assert not turn_actions.interaction
    assert not turn_actions.dialog

    # Make sure the list is empty when no actions
    assert not turn_actions.to_list()

    # Add in interaction action and make sure it is in the list
    turn_actions.interaction = interaction_action
    assert len(turn_actions.to_list()) == 1
    assert turn_actions.to_list()[0] == interaction_action

    # Add the dialog action and make sure it is at the end of the list
    turn_actions.dialog = dialog_action
    assert len(turn_actions.to_list()) == 2
    assert turn_actions.to_list()[0] == interaction_action
    assert turn_actions.to_list()[1] == dialog_action

    # Remove the interaction action and make sure the dialog action is in the list
    turn_actions.interaction = None
    assert len(turn_actions.to_list()) == 1
    assert turn_actions.to_list()[0] == dialog_action

    # Add the interaction action back and make sure the list order is still correct
    turn_actions.interaction = interaction_action
    assert len(turn_actions.to_list()) == 2
    assert turn_actions.to_list()[0] == interaction_action
    assert turn_actions.to_list()[1] == dialog_action
