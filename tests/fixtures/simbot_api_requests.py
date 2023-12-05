import uuid
from pathlib import Path
from typing import Any


def _get_metadata_file_name(simbot_game_metadata_dir: Path) -> str:
    """Get the auxiliary metadata file from the directory."""
    metadata_file_path = next(simbot_game_metadata_dir.iterdir())
    game_metadata_file_name = metadata_file_path.name
    if metadata_file_path.is_dir():
        metadata_file_path = next(metadata_file_path.iterdir())
        game_metadata_file_name = f"{game_metadata_file_name}/{metadata_file_path.name}"

    return game_metadata_file_name


class SimBotRequestCases:
    def case_without_previous_actions(self, simbot_game_metadata_dir: Path) -> dict[str, Any]:
        """Example request without any previous actions."""
        request_body = {
            "header": {
                "predictionRequestId": str(uuid.uuid1()),
                "sessionId": "session_19099",
            },
            "request": {
                "sensors": [
                    {
                        "type": "SpeechRecognition",
                        "recognition": {
                            "tokens": [
                                {
                                    "value": "turn on the computer.",
                                    "confidence": {"score": 0.98, "bin": "HIGH"},
                                },
                            ]
                        },
                    },
                    {
                        "type": "GameMetaData",
                        "metaData": {
                            "uri": f"efs://{_get_metadata_file_name(simbot_game_metadata_dir)}"
                        },
                    },
                ],
                "previousActions": [],
            },
        }

        return request_body

    def case_with_single_previous_action(self, simbot_game_metadata_dir: Path) -> dict[str, Any]:
        """Example request without single previous action."""
        request_body = {
            "header": {
                "predictionRequestId": str(uuid.uuid1()),
                "sessionId": "session_19099",
            },
            "request": {
                "sensors": [
                    {
                        "type": "SpeechRecognition",
                        "recognition": {
                            "tokens": [
                                {
                                    "value": "turn on the computer.",
                                    "confidence": {"score": 0.98, "bin": "HIGH"},
                                },
                            ]
                        },
                    },
                    {
                        "type": "GameMetaData",
                        "metaData": {
                            "uri": f"efs://{_get_metadata_file_name(simbot_game_metadata_dir)}"
                        },
                    },
                ],
                "previousActions": [
                    {"id": "0", "type": "Look", "success": False, "errorType": "InvalidCommand"}
                ],
            },
        }

        return request_body

    def case_followup_without_speech(self, simbot_game_metadata_dir: Path) -> dict[str, Any]:
        """Example request without receiving any additional speech input."""
        request_body = {
            "header": {
                "predictionRequestId": str(uuid.uuid1()),
                "sessionId": "session_19099",
            },
            "request": {
                "sensors": [
                    {
                        "type": "GameMetaData",
                        "metaData": {
                            "uri": f"efs://{_get_metadata_file_name(simbot_game_metadata_dir)}"
                        },
                    },
                ],
                "previousActions": [
                    {"id": "0", "type": "Look", "success": False, "errorType": "InvalidCommand"}
                ],
            },
        }

        return request_body
