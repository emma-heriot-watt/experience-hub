from typing import Any

from pytest_cases import parametrize_with_cases

from emma_experience_hub.datamodels.simbot import SimBotRequest
from emma_experience_hub.datamodels.simbot.actions import SimBotAuxiliaryMetadataAction
from tests.fixtures.simbot_api_requests import SimBotRequestCases


@parametrize_with_cases("request_body", cases=SimBotRequestCases)
def test_request_json_parses_without_error(request_body: dict[str, Any]) -> None:
    parsed_request = SimBotRequest.parse_obj(request_body)
    assert parsed_request


@parametrize_with_cases("request_body", cases=SimBotRequestCases)
def test_auxiliary_metadata_automatically_parsed(request_body: dict[str, Any]) -> None:
    parsed_request = SimBotRequest.parse_obj(request_body)
    assert parsed_request

    assert isinstance(parsed_request.auxiliary_metadata, SimBotAuxiliaryMetadataAction)
