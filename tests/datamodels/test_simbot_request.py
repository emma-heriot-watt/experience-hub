from typing import Any

from pytest_cases import parametrize_with_cases

from emma_experience_hub.datamodels.simbot import SimBotRequest, SimBotSessionTurn
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotAuxiliaryMetadataPayload,
    SimBotSpeechRecognitionPayload,
)
from tests.fixtures.simbot_api_requests import SimBotRequestCases


@parametrize_with_cases("request_body", cases=SimBotRequestCases)
def test_request_json_parses_without_error(request_body: dict[str, Any]) -> None:
    parsed_request = SimBotRequest.parse_obj(request_body)
    assert parsed_request

    assert isinstance(parsed_request.auxiliary_metadata, SimBotAuxiliaryMetadataPayload)

    if parsed_request.speech_recognition:
        assert isinstance(parsed_request.speech_recognition, SimBotSpeechRecognitionPayload)


@parametrize_with_cases("request_body", cases=SimBotRequestCases)
def test_request_successfully_parses_to_session_turn(request_body: dict[str, Any]) -> None:
    parsed_request = SimBotRequest.parse_obj(request_body)
    turn = SimBotSessionTurn.new_from_simbot_request(parsed_request, 0)

    assert turn
