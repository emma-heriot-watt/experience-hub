from typing import Any

from pytest_cases import parametrize_with_cases

from emma_experience_hub.api.controllers import SimBotController
from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.datamodels.simbot import SimBotRequest
from tests.fixtures.simbot_api_requests import SimBotRequestCases


@parametrize_with_cases("request_body", cases=SimBotRequestCases)
def test_simbot_api(
    request_body: dict[str, Any],
    simbot_settings: SimBotSettings,
) -> None:
    simbot_request = SimBotRequest.parse_obj(request_body)
    controller = SimBotController.from_simbot_settings(simbot_settings)
    controller.handle_request_from_simbot_arena(simbot_request)
