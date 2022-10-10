import os
import uuid
from pathlib import Path
from typing import Any

from pytest_cases import fixture


class SimBotRequestCases:
    def case_without_previous_actions(self, simbot_game_metadata_dir: Path) -> dict[str, Any]:
        """Example request without any previous actions."""
        self._set_env_vars(simbot_game_metadata_dir)
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
                        "metaData": {
                            "uri": f"efs://{self._get_metadata_file_name(simbot_game_metadata_dir)}"
                        },
                    },
                ],
                "previousActions": [],
            },
        }

        return request_body

    def case_with_single_previous_action(self, simbot_game_metadata_dir: Path) -> dict[str, Any]:
        """Example request without single previous action."""
        self._set_env_vars(simbot_game_metadata_dir)
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
                        "metaData": {
                            "uri": f"efs://{self._get_metadata_file_name(simbot_game_metadata_dir)}"
                        },
                    },
                ],
                "previousActions": [
                    {"id": None, "type": "Look", "success": False, "errorType": "InvalidCommand"}
                ],
            },
        }

        return request_body

    def case_followup_without_speech(self, simbot_game_metadata_dir: Path) -> dict[str, Any]:
        """Example request without receiving any additional speech input."""
        self._set_env_vars(simbot_game_metadata_dir)
        request_body = {
            "header": {
                "predictionRequestId": str(uuid.uuid1()),  # Request ID - unique per request
                "sessionId": "session_19099",  # Session ID - unique per session
            },
            "request": {
                "sensors": [
                    {
                        "type": "GameMetaData",
                        "metaData": {
                            "uri": f"efs://{self._get_metadata_file_name(simbot_game_metadata_dir)}"
                        },
                    },
                ],
                "previousActions": [
                    {"id": None, "type": "Look", "success": False, "errorType": "InvalidCommand"}
                ],
            },
        }

        return request_body

    def _set_env_vars(self, simbot_game_metadata_dir: Path) -> None:
        """Set the necessary environment variables."""
        os.environ["SIMBOT_AUXILIARY_METADATA_DIR"] = str(simbot_game_metadata_dir.resolve())
        os.environ["SIMBOT_AUXILIARY_METADATA_CACHE_DIR"] = str(simbot_game_metadata_dir.resolve())

    def _get_metadata_file_name(self, simbot_game_metadata_dir: Path) -> str:
        """Get the auxiliary metadata file from the directory."""
        metadata_file_path = next(simbot_game_metadata_dir.iterdir())
        game_metadata_file_name = metadata_file_path.name
        if metadata_file_path.is_dir():
            metadata_file_path = next(metadata_file_path.iterdir())
            game_metadata_file_name = f"{game_metadata_file_name}/{metadata_file_path.name}"

        return game_metadata_file_name


@fixture(scope="session")
def simbot_session_db_turn() -> str:
    # return '{"session_id": "amzn1.echo-api.session.dd7b95cd-bc64-49d1-81ac-57e885160c20_4", "prediction_request_id": "f9644d5f-7745-490e-abca-147b7cda417c", "idx": 1, "timestamp": {"start": "2022-10-04T17:36:52.996641", "end": null}, "current_room": "SmallOffice", "unique_room_names": ["Reception", "MainOffice", "Lab2", "SmallOffice", "Warehouse", "BreakRoom", "Lab1"], "viewpoints": ["MainOffice_6", "Lab1_6", "Warehouse_5", "Reception_4", "BreakRoom_3", "Reception_1", "Warehouse_2", "Lab1_7", "SmallOffice_8", "Reception_6", "MainOffice_7", "Lab2_4", "MainOffice_5", "Warehouse_3", "SmallOffice_1", "BreakRoom_1", "Lab2_8", "MainOffice_2", "Lab2_7", "BreakRoom_6", "Lab2_1", "Warehouse_4", "BreakRoom_7", "SmallOffice_2", "Lab2_3", "Reception_7", "Lab2_2", "BreakRoom_5", "Lab1_1", "BreakRoom_8", "MainOffice_1", "BreakRoom_4", "MainOffice_8", "Lab1_4", "SmallOffice_6", "SmallOffice_3", "Lab1_3", "Lab1_5", "Lab1_2", "SmallOffice_5", "Reception_2", "SmallOffice_4", "Reception_8", "BreakRoom_2", "SmallOffice_7", "Lab2_6", "MainOffice_4", "Reception_3", "MainOffice_3", "Warehouse_1", "Lab2_5", "Lab1_8", "Reception_5"], "speech": {"tokens": [{"value": "pick", "confidence": {"score": 0.85, "bin": "HIGH"}}, {"value": "up", "confidence": {"score": 0.88, "bin": "HIGH"}}, {"value": "ball", "confidence": {"score": 0.802, "bin": "HIGH"}}]}, "auxiliary_metadata_uri": "efs://amzn1.echo-api.session.dd7b95cd-bc64-49d1-81ac-57e885160c20_4/e7c20078863942d5a4a54e76cefa1e0c_metadata.json", "intent": {"type": "<act>", "object_name": null}, "actions": [{"type": "pickup", "status": null, "pickup": {"object": {"colorImageIndex": 1, "mask": "", "name": "Broken Radio"}}}, {"type": "dialog", "status": null, "dialog": {"value": "Ok, what next?", "intent": null}}], "raw_output": "Pickup Broken Radio <frame_token_1>.</s>"}'
    return '{"session_id": "amzn1.echo-api.session.dd7b95cd-bc64-49d1-81ac-57e885160c20_4", "prediction_request_id": "f9644d5f-7745-490e-abca-147b7cda417c", "idx": 1, "timestamp": {"start": "2022-10-04T17:36:52.996641", "end": null}, "current_room": "SmallOffice", "unique_room_names": ["Reception", "MainOffice", "Lab2", "SmallOffice", "Warehouse", "BreakRoom", "Lab1"], "viewpoints": ["MainOffice_6", "Lab1_6", "Warehouse_5", "Reception_4", "BreakRoom_3", "Reception_1", "Warehouse_2", "Lab1_7", "SmallOffice_8", "Reception_6", "MainOffice_7", "Lab2_4", "MainOffice_5", "Warehouse_3", "SmallOffice_1", "BreakRoom_1", "Lab2_8", "MainOffice_2", "Lab2_7", "BreakRoom_6", "Lab2_1", "Warehouse_4", "BreakRoom_7", "SmallOffice_2", "Lab2_3", "Reception_7", "Lab2_2", "BreakRoom_5", "Lab1_1", "BreakRoom_8", "MainOffice_1", "BreakRoom_4", "MainOffice_8", "Lab1_4", "SmallOffice_6", "SmallOffice_3", "Lab1_3", "Lab1_5", "Lab1_2", "SmallOffice_5", "Reception_2", "SmallOffice_4", "Reception_8", "BreakRoom_2", "SmallOffice_7", "Lab2_6", "MainOffice_4", "Reception_3", "MainOffice_3", "Warehouse_1", "Lab2_5", "Lab1_8", "Reception_5"], "speech": {"tokens": [{"value": "pick", "confidence": {"score": 0.85, "bin": "HIGH"}}, {"value": "up", "confidence": {"score": 0.88, "bin": "HIGH"}}, {"value": "ball", "confidence": {"score": 0.802, "bin": "HIGH"}}]}, "auxiliary_metadata_uri": "efs://amzn1.echo-api.session.dd7b95cd-bc64-49d1-81ac-57e885160c20_4/e7c20078863942d5a4a54e76cefa1e0c_metadata.json", "intent": {"type": "<act>", "object_name": null}, "actions": [{"type": "pickup", "status": null, "pickup": {"object": {"colorImageIndex": 1, "mask": null, "name": "Broken Radio"}}}, {"type": "dialog", "status": null, "dialog": {"value": "Ok, what next?", "intent": null}}], "raw_output": "Pickup Broken Radio <frame_token_1>.</s>"}'
