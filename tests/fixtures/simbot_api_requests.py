import uuid
from pathlib import Path
from typing import Any


class SimBotRequestCases:
    def case_without_previous_actions(self, simbot_game_metadata_dir: Path) -> dict[str, Any]:
        """Example request without any previous actions."""
        game_metadata_file_name = next(simbot_game_metadata_dir.iterdir()).name

        request_body = {
            "header": {
                "predictionRequestId": str(uuid.uuid1()),  # Request ID - unique per request
                "sessionId": "session_19099",  # Session ID - unique per session
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
                        "metaData": {"uri": f"efs://{game_metadata_file_name}"},
                    },
                ],
                "previousActions": [],
            },
        }

        return request_body
