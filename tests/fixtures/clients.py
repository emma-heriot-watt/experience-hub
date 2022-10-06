import json
import uuid
from collections.abc import Generator
from pathlib import Path

import httpx
from pydantic import AnyHttpUrl
from pytest_cases import fixture
from pytest_httpx import HTTPXMock

from emma_experience_hub.api.clients import UtteranceGeneratorClient
from emma_experience_hub.api.clients.simbot import SimBotSessionDbClient
from emma_experience_hub.datamodels.simbot.payloads import SimBotSpeechRecognitionPayload
from emma_experience_hub.datamodels.simbot.session import (
    SimBotAuxiliaryMetadataUri,
    SimBotSessionTurn,
    SimBotSessionTurnTimestamp,
)


@fixture
def dynamo_db_client() -> SimBotSessionDbClient:
    return SimBotSessionDbClient("us-east-1", "MEMORY_TABLE_test")


@fixture
def session_turn(simbot_game_metadata_dir: Path) -> SimBotSessionTurn:
    game_metadata_file_name = next(simbot_game_metadata_dir.iterdir())

    with open(game_metadata_file_name) as in_file:
        metadata = json.load(in_file)

    return SimBotSessionTurn(
        prediction_request_id=str(uuid.uuid1()),
        session_id="session_19099",
        idx=0,
        timestamp=SimBotSessionTurnTimestamp(),
        auxiliary_metadata_uri=SimBotAuxiliaryMetadataUri(
            url=f"efs://{game_metadata_file_name}", scheme="efs"
        ),
        speech=SimBotSpeechRecognitionPayload.parse_obj(
            {
                "tokens": [
                    {
                        "value": "turn on the computer.",
                        "confidence": {"score": 0.98, "bin": "HIGH"},
                    },
                ]
            },
        ),
        viewpoints=metadata["viewPoints"],
        current_room=metadata["robotInfo"][0]["currentRoom"],
        unique_room_names={viewpoint.split("_")[0] for viewpoint in metadata["viewPoints"]},
    )


@fixture
def utterance_generator_client(
    httpx_mock: HTTPXMock,
) -> Generator[UtteranceGeneratorClient, None, None]:
    def custom_response(request: httpx.Request) -> httpx.Response:  # noqa: WPS430
        return httpx.Response(status_code=200, json="utterance_go_here")

    httpx_mock.add_callback(custom_response)
    assert httpx.post("http://localhost").json() == "utterance_go_here"
    yield UtteranceGeneratorClient(endpoint=AnyHttpUrl(url="http://localhost", scheme="http"))
