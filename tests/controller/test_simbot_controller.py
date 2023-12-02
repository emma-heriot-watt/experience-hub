from typing import Any

from pytest_cases import parametrize, parametrize_with_cases

from emma_experience_hub.api.clients.simbot import SimbotActionPredictionClient
from emma_experience_hub.api.controllers import SimBotController
from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.datamodels.simbot import SimBotRequest
from tests.fixtures.clients import (
    mock_policy_response_goto_room,
    mock_policy_response_search,
    mock_policy_response_toggle_computer,
)
from tests.fixtures.simbot_api_requests import SimBotRequestCases


@parametrize_with_cases("request_body", cases=SimBotRequestCases.case_without_previous_actions)
@parametrize(
    "mock_policy_responses",
    [
        mock_policy_response_toggle_computer,
        mock_policy_response_goto_room,
        mock_policy_response_search,
    ],
)
def test_simbot_api(
    request_body: dict[str, Any],
    simbot_settings: SimBotSettings,
    mock_feature_extraction_response: Any,
    mock_policy_responses: Any,
) -> None:
    """Test the SimBot API."""
    simbot_request = SimBotRequest.parse_obj(request_body)
    controller = SimBotController.from_simbot_settings(simbot_settings)
    response = controller.handle_request_from_simbot_arena(simbot_request)
    assert response.actions[0].raw_output is not None
    assert response.actions[0].raw_output == SimbotActionPredictionClient.generate()
