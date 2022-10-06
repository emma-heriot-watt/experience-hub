from pytest_cases import param_fixture

from emma_experience_hub.constants.simbot import load_arena_definitions
from emma_experience_hub.datamodels.simbot.actions import SimBotActionType


simbot_room_name = param_fixture(
    "simbot_room_name", load_arena_definitions()["room_names"], scope="session"
)


simbot_object_name = param_fixture(
    "simbot_object_name",
    ["Apple", "Sticky Note", "Machine Panel"],
    scope="session",
)

simbot_interaction_action = param_fixture(
    "simbot_interaction_action",
    [action.name for action in SimBotActionType.object_interaction()],
    scope="session",
)
