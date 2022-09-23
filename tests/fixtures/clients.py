import json
import uuid
from pathlib import Path

from pytest_cases import fixture

from emma_experience_hub.api.clients.simbot_session_db import (
    SimBotSessionDbClient,
    SimBotSessionTurn,
)
from emma_experience_hub.datamodels.simbot.session import (
    SimBotSessionTurnTimestamp,
    SimBotSpeechRecognitionAction,
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
        auxiliary_metadata_uri=f"efs://{game_metadata_file_name}",
        speech=SimBotSpeechRecognitionAction.parse_obj(
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
