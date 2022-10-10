import itertools

from pytest_cases import param_fixture

from emma_experience_hub.constants.simbot import (  # get_simbot_object_label_to_class_name_map,
    get_simbot_room_names,
)
from emma_experience_hub.datamodels.simbot.actions import SimBotActionType


simbot_room_name = param_fixture(
    "simbot_room_name",
    sorted(itertools.chain(get_simbot_room_names(), get_simbot_room_names(lowercase=True))),
    scope="session",
)


simbot_object_name = param_fixture(
    "simbot_object_name",
    ["Apple", "Sticky Note", "Machine Panel"],
    # sorted(get_simbot_object_label_to_class_name_map().keys()),
    scope="session",
)

simbot_interaction_action = param_fixture(
    "simbot_interaction_action",
    [action.name for action in SimBotActionType.object_interaction()],
    scope="session",
)
