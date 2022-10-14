import os
import random
import uuid
from pathlib import Path
from typing import Any

from pytest_cases import fixture, parametrize

from emma_experience_hub.datamodels.simbot import (
    SimBotIntentType,
    SimBotSession,
    SimBotSessionTurn,
)


def _set_env_vars(simbot_game_metadata_dir: Path) -> None:
    """Set the necessary environment variables."""
    os.environ["SIMBOT_AUXILIARY_METADATA_DIR"] = str(simbot_game_metadata_dir.resolve())
    os.environ["SIMBOT_AUXILIARY_METADATA_CACHE_DIR"] = str(simbot_game_metadata_dir.resolve())


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
        _set_env_vars(simbot_game_metadata_dir)
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
        _set_env_vars(simbot_game_metadata_dir)
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
                            "uri": f"efs://{_get_metadata_file_name(simbot_game_metadata_dir)}"
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
        _set_env_vars(simbot_game_metadata_dir)
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
                            "uri": f"efs://{_get_metadata_file_name(simbot_game_metadata_dir)}"
                        },
                    },
                ],
                "previousActions": [
                    {"id": None, "type": "Look", "success": False, "errorType": "InvalidCommand"}
                ],
            },
        }

        return request_body


class SimBotSessionCases:
    session_id = "amzn1.echo-api.session.3f55df67-01ac-48ad-aa5b-380dcd22b837_5"
    viewpoints = ["Warehouse_2", "SmallOffice_6", "Reception_4", "Lab2_3", "Lab1_8"]
    unique_room_names = [
        "BreakRoom",
        "Lab2",
        "Reception",
        "SmallOffice",
        "Warehouse",
        "Lab1",
        "MainOffice",
    ]
    current_room = "Lab1"
    start_time = "2022-10-10T14:20:{0}.043774"

    @parametrize(
        "include_clarify_question_before_act",
        [False, True],
        ids=["act_without_clarify_at_start", "act_after_clarify_at_start"],
    )
    def case_just_one_action(
        self,
        simbot_game_metadata_dir: Path,
        include_clarify_question_before_act: bool,
    ) -> tuple[SimBotSession, int]:
        _set_env_vars(simbot_game_metadata_dir)

        turns: list[SimBotSessionTurn] = []

        if include_clarify_question_before_act:
            turns.append(
                self._get_clarification_question_turn(simbot_game_metadata_dir, len(turns))
            )

        turns.append(
            self._get_look_around_turn(
                simbot_game_metadata_dir,
                len(turns),
                include_speech=include_clarify_question_before_act or not turns,
                include_end_of_trajectory=False,
            )
        )

        return SimBotSession(session_id=self.session_id, turns=turns), len(turns)

    @parametrize(
        "include_clarify_question_before_act",
        [False, True],
        ids=["without_clarify_at_start", "after_clarify_at_start"],
    )
    @parametrize("num_actions", [1, 2, 3, 4, 5], idgen="{num_actions}_actions")
    def case_consecutive_actions_from_one_utterance(
        self,
        simbot_game_metadata_dir: Path,
        num_actions: int,
        include_clarify_question_before_act: bool,
    ) -> tuple[SimBotSession, int]:
        _set_env_vars(simbot_game_metadata_dir)

        turns: list[SimBotSessionTurn] = []

        for turn_idx in range(num_actions):
            # Include clarify question turn if turn idx is 0
            if include_clarify_question_before_act and turn_idx == 0:
                turns.append(
                    self._get_clarification_question_turn(simbot_game_metadata_dir, turn_idx)
                )
                continue

            if turn_idx > 0 and turns[turn_idx - 1].is_clarify_intent:
                turns.append(
                    self._get_look_around_turn(
                        simbot_game_metadata_dir,
                        turn_idx,
                        include_speech=True,
                        include_end_of_trajectory=turn_idx == num_actions - 1,
                    )
                )
                continue

            turns.append(
                self._get_look_around_turn(
                    simbot_game_metadata_dir,
                    turn_idx,
                    include_speech=turn_idx == 0,
                    include_end_of_trajectory=turn_idx == num_actions - 1,
                )
            )

        assert len(turns) == num_actions

        return SimBotSession(session_id=self.session_id, turns=turns), len(turns)

    @parametrize("num_actions", [2, 3, 4, 5], idgen="{num_actions}_actions")
    def case_consecutive_interrupted_actions_before_returning_dialog(
        self, simbot_game_metadata_dir: Path, num_actions: int
    ) -> tuple[SimBotSession, int]:
        _set_env_vars(simbot_game_metadata_dir)

        turns: list[SimBotSessionTurn] = []

        for turn_idx in range(num_actions):
            turns.append(
                self._get_goto_sink_turn(
                    simbot_game_metadata_dir,
                    turn_idx,
                    include_speech=True,
                    include_end_of_trajectory=True,
                )
            )

        return SimBotSession(session_id=self.session_id, turns=turns), 1

    @parametrize(
        "num_actions_before_interruption",
        [1, 2, 3, 4],
        idgen="{num_actions_before_interruption}_actions_before_interruption",
    )
    @parametrize(
        "num_actions_since_interruption",
        [1, 2, 3, 4],
        idgen="{num_actions_since_interruption}_actions_since_interruption",
    )
    def case_interrupted_in_middle_of_action_sequence(
        self,
        simbot_game_metadata_dir: Path,
        num_actions_before_interruption: int,
        num_actions_since_interruption: int,
    ) -> tuple[SimBotSession, int]:
        _set_env_vars(simbot_game_metadata_dir)

        turns: list[SimBotSessionTurn] = []

        # Populate with actions before being interrupted
        for turn_idx_before in range(num_actions_before_interruption):
            turns.append(
                self._get_look_around_turn(
                    simbot_game_metadata_dir,
                    len(turns),
                    include_speech=turn_idx_before == 0,
                    include_end_of_trajectory=False,
                )
            )

        for turn_idx_after in range(num_actions_since_interruption):
            turns.append(
                self._get_goto_sink_turn(
                    simbot_game_metadata_dir,
                    len(turns),
                    include_speech=turn_idx_after == 0,
                    include_end_of_trajectory=False,
                )
            )

        return (
            SimBotSession(session_id=self.session_id, turns=turns),
            num_actions_since_interruption,
        )

    @parametrize(
        "num_actions_before_non_actionble_utterance",
        [1, 2],
        idgen="{num_actions_before_non_actionble_utterance}_actions_before_non_actionable_utterance",
    )
    @parametrize(
        "num_actions_since_non_actionable_utterance",
        [1, 2],
        idgen="{num_actions_since_non_actionable_utterance}_actions_since_non_actionable_utterance",
    )
    @parametrize(
        "num_consecutive_non_actionable_utterances",
        [1, 2],
        idgen="{num_consecutive_non_actionable_utterances}_consecutive_non_actionable_utterances",
    )
    @parametrize(
        "is_first_non_actionable_utterance_an_interruption",
        [True, False],
        ids=[
            "is_interrupted_by_non_actionable_utterance",
            "not_interrupted_by_non_actionable_utterance",
        ],
    )
    @parametrize(
        "is_clarify_after_non_actionable_utterances",
        [True, False],
        ids=[
            "clarify_after_non_actionable_utterances",
            "not_clarify_after_non_actionable_utterance",
        ],
    )
    def case_separated_by_non_actionable_utterance(
        self,
        simbot_game_metadata_dir: Path,
        num_actions_before_non_actionble_utterance: int,
        num_actions_since_non_actionable_utterance: int,
        num_consecutive_non_actionable_utterances: int,
        is_first_non_actionable_utterance_an_interruption: bool,
        is_clarify_after_non_actionable_utterances: bool,
    ) -> tuple[SimBotSession, int]:
        _set_env_vars(simbot_game_metadata_dir)

        turns: list[SimBotSessionTurn] = []

        # Populate with actions before being interrupted
        for turn_idx_before in range(num_actions_before_non_actionble_utterance):
            turns.append(
                self._get_look_around_turn(
                    simbot_game_metadata_dir,
                    len(turns),
                    include_speech=turn_idx_before == 0,
                    # Include the end of trajectory if desired by test
                    include_end_of_trajectory=is_first_non_actionable_utterance_an_interruption
                    and turn_idx_before == num_actions_before_non_actionble_utterance - 1,
                )
            )

        if not is_first_non_actionable_utterance_an_interruption:
            turns.append(
                self._get_end_of_trajectory_dialog_turn(simbot_game_metadata_dir, len(turns))
            )

        for _ in range(num_consecutive_non_actionable_utterances):
            turns.append(self._get_non_actionable_turn(simbot_game_metadata_dir, len(turns)))

        turns_after_interruption = []
        if is_clarify_after_non_actionable_utterances:
            turns_after_interruption = self._get_clarify_question_then_consecutive_actions(
                simbot_game_metadata_dir,
                len(turns),
                num_actions_since_non_actionable_utterance,
            )
        else:
            turns_after_interruption = [
                self._get_goto_sink_turn(
                    simbot_game_metadata_dir,
                    len(turns),
                    include_speech=turn_idx_after == 0,
                    include_end_of_trajectory=False,
                )
                for turn_idx_after in range(num_actions_since_non_actionable_utterance)
            ]

        turns.extend(turns_after_interruption)

        assert turns_after_interruption

        return (
            SimBotSession(session_id=self.session_id, turns=turns),
            len(turns_after_interruption),
        )

    @parametrize("num_sequences", [2, 3, 4, 5], idgen="{num_sequences}_sequences")
    def case_consecutive_complete_action_sequences(
        self, simbot_game_metadata_dir: Path, num_sequences: int
    ) -> tuple[SimBotSession, int]:
        _set_env_vars(simbot_game_metadata_dir)

        turns: list[SimBotSessionTurn] = []

        for sequence_idx in range(num_sequences):
            sequence_length = (
                num_sequences if sequence_idx == num_sequences - 1 else random.randint(1, 4)
            )

            chosen_action = random.choice([self._get_look_around_turn, self._get_goto_sink_turn])

            for turn_idx in range(sequence_length):
                turns.append(
                    chosen_action(
                        simbot_game_metadata_dir,
                        len(turns),
                        include_speech=turn_idx == 0,
                        include_end_of_trajectory=turn_idx == sequence_length - 1,
                    )
                )

            if sequence_idx != num_sequences - 1:
                turns.append(
                    self._get_end_of_trajectory_dialog_turn(simbot_game_metadata_dir, len(turns))
                )

        return SimBotSession(session_id=self.session_id, turns=turns), num_sequences

    @parametrize("num_sequences", [2, 3, 4, 5], idgen="{num_sequences}_sequences")
    def case_consecutive_complete_clarified_action_sequences(
        self, simbot_game_metadata_dir: Path, num_sequences: int
    ) -> tuple[SimBotSession, int]:
        _set_env_vars(simbot_game_metadata_dir)

        turns: list[SimBotSessionTurn] = []

        for sequence_idx in range(num_sequences):
            sequence_length = (
                num_sequences if sequence_idx == num_sequences - 1 else random.randint(2, 5)
            )

            chosen_action = random.choice([self._get_look_around_turn, self._get_goto_sink_turn])

            for turn_idx in range(sequence_length):
                if turn_idx == 0:
                    turns.append(
                        self._get_clarification_question_turn(simbot_game_metadata_dir, len(turns))
                    )
                else:
                    turns.append(
                        chosen_action(
                            simbot_game_metadata_dir,
                            len(turns),
                            # Include speech after the clarify action
                            include_speech=turn_idx == 1,
                            include_end_of_trajectory=turn_idx == sequence_length - 1,
                        )
                    )

            if sequence_idx != num_sequences - 1:
                turns.append(
                    self._get_end_of_trajectory_dialog_turn(simbot_game_metadata_dir, len(turns))
                )

        return SimBotSession(session_id=self.session_id, turns=turns), num_sequences

    def case_consecutive_action_sequences_then_clarify_for_next(
        self, simbot_game_metadata_dir: Path
    ) -> tuple[SimBotSession, int]:
        _set_env_vars(simbot_game_metadata_dir)

        turns: list[SimBotSessionTurn] = self.case_consecutive_complete_action_sequences(
            simbot_game_metadata_dir, 2
        )[0].turns

        # Add end of trajectory turn to end of previous sequences
        turns.append(self._get_end_of_trajectory_dialog_turn(simbot_game_metadata_dir, len(turns)))

        turns.append(self._get_clarification_question_turn(simbot_game_metadata_dir, len(turns)))
        turns.append(
            self._get_look_around_turn(
                simbot_game_metadata_dir,
                len(turns),
                include_speech=True,
                include_end_of_trajectory=False,
            )
        )

        return SimBotSession(session_id=self.session_id, turns=turns), 2

    def _get_look_around_turn(
        self,
        simbot_game_metadata_dir: Path,
        turn_idx: int,
        include_speech: bool,
        include_end_of_trajectory: bool,
    ) -> SimBotSessionTurn:
        speech = (
            {
                "tokens": [
                    {"value": "go", "confidence": {"score": 0.729, "bin": "HIGH"}},
                    {"value": "to", "confidence": {"score": 0.844, "bin": "HIGH"}},
                    {"value": "the", "confidence": {"score": 0.711, "bin": "HIGH"}},
                    {"value": "sink", "confidence": {"score": 0.315, "bin": "HIGH"}},
                ]
            }
            if include_speech
            else None
        )

        raw_output = "look around <stop>.</s>" if include_end_of_trajectory else "look around.</s>"

        return SimBotSessionTurn.parse_obj(
            {
                "session_id": "amzn1.echo-api.session.3f55df67-01ac-48ad-aa5b-380dcd22b837_5",
                "prediction_request_id": str(uuid.uuid1()),
                "idx": turn_idx,
                "timestamp": {"start": self.start_time.format(turn_idx), "end": None},
                "current_room": self.current_room,
                "unique_room_names": self.unique_room_names,
                "viewpoints": self.viewpoints,
                "speech": speech,
                "auxiliary_metadata_uri": f"efs://{_get_metadata_file_name(simbot_game_metadata_dir)}",
                "intent": {"type": "<act>", "object_name": None},
                "action": {
                    "type": "Look",
                    "look": {"direction": "Around", "magnitude": 100},
                    "status": None,
                },
                "raw_output": raw_output,
            }
        )

    def _get_goto_sink_turn(
        self,
        simbot_game_metadata_dir: Path,
        turn_idx: int,
        include_speech: bool,
        include_end_of_trajectory: bool,
    ) -> SimBotSessionTurn:
        speech = (
            {
                "tokens": [
                    {"value": "go", "confidence": {"score": 0.729, "bin": "HIGH"}},
                    {"value": "to", "confidence": {"score": 0.844, "bin": "HIGH"}},
                    {"value": "the", "confidence": {"score": 0.711, "bin": "HIGH"}},
                    {"value": "sink", "confidence": {"score": 0.315, "bin": "HIGH"}},
                ]
            }
            if include_speech
            else None
        )

        raw_output = "goto sink <stop>.</s>" if include_end_of_trajectory else "goto sink.</s>"

        return SimBotSessionTurn.parse_obj(
            {
                "session_id": "amzn1.echo-api.session.3f55df67-01ac-48ad-aa5b-380dcd22b837_5",
                "prediction_request_id": str(uuid.uuid1()),
                "idx": turn_idx,
                "timestamp": {"start": self.start_time.format(turn_idx), "end": None},
                "current_room": self.current_room,
                "unique_room_names": self.unique_room_names,
                "viewpoints": self.viewpoints,
                "speech": speech,
                "auxiliary_metadata_uri": f"efs://{_get_metadata_file_name(simbot_game_metadata_dir)}",
                "intent": {"type": "<act>", "object_name": None},
                "action": {
                    "type": "Goto",
                    "status": None,
                    "goto": {"object": {"colorImageIndex": 0, "mask": None, "name": "sink"}},
                },
                "raw_output": raw_output,
            }
        )

    def _get_clarification_question_turn(
        self, simbot_game_metadata_dir: Path, turn_idx: int
    ) -> SimBotSessionTurn:
        return SimBotSessionTurn.parse_obj(
            {
                "session_id": self.session_id,
                "prediction_request_id": str(uuid.uuid1()),
                "idx": turn_idx,
                "timestamp": {"start": self.start_time.format(turn_idx), "end": None},
                "current_room": self.current_room,
                "unique_room_names": self.unique_room_names,
                "viewpoints": self.viewpoints,
                "speech": {
                    "tokens": [
                        {"value": "go", "confidence": {"score": 0.729, "bin": "HIGH"}},
                        {"value": "to", "confidence": {"score": 0.844, "bin": "HIGH"}},
                        {"value": "the", "confidence": {"score": 0.711, "bin": "HIGH"}},
                        {"value": "sink", "confidence": {"score": 0.315, "bin": "HIGH"}},
                    ]
                },
                "auxiliary_metadata_uri": f"efs://{_get_metadata_file_name(simbot_game_metadata_dir)}",
                "intent": {"type": "<clarify><location>", "object_name": None},
                "action": {
                    "type": "Dialog",
                    "status": None,
                    "dialog": {"value": "where is the sink?"},
                },
                "raw_output": "where is the sink?",
            }
        )

    def _get_end_of_trajectory_dialog_turn(
        self, simbot_game_metadata_dir: Path, turn_idx: int
    ) -> SimBotSessionTurn:
        return SimBotSessionTurn.parse_obj(
            {
                "session_id": self.session_id,
                "prediction_request_id": str(uuid.uuid1()),
                "idx": turn_idx,
                "timestamp": {"start": self.start_time.format(turn_idx), "end": None},
                "current_room": self.current_room,
                "unique_room_names": self.unique_room_names,
                "viewpoints": self.viewpoints,
                "speech": None,
                "auxiliary_metadata_uri": f"efs://{_get_metadata_file_name(simbot_game_metadata_dir)}",
                "intent": {"type": "<end_of_trajectory>", "object_name": None},
                "action": {
                    "type": "Dialog",
                    "status": None,
                    "dialog": {"value": "Done!"},
                },
                "raw_output": "Done!",
            }
        )

    def _get_non_actionable_turn(
        self, simbot_game_metadata_dir: Path, turn_idx: int
    ) -> SimBotSessionTurn:
        all_non_actionable_intents = [
            intent for intent in SimBotIntentType if not intent.is_actionable
        ]

        speech = {
            "tokens": [
                {"value": "blah", "confidence": {"score": 0.729, "bin": "HIGH"}},
                {"value": "blah", "confidence": {"score": 0.844, "bin": "HIGH"}},
            ]
        }

        return SimBotSessionTurn.parse_obj(
            {
                "session_id": self.session_id,
                "prediction_request_id": str(uuid.uuid1()),
                "idx": turn_idx,
                "timestamp": {"start": self.start_time.format(turn_idx), "end": None},
                "current_room": self.current_room,
                "unique_room_names": self.unique_room_names,
                "viewpoints": self.viewpoints,
                "speech": speech,
                "auxiliary_metadata_uri": f"efs://{_get_metadata_file_name(simbot_game_metadata_dir)}",
                "intent": {
                    "type": random.choice(all_non_actionable_intents).value,
                    "object_name": None,
                },
                "action": {
                    "type": "Dialog",
                    "status": None,
                    "dialog": {"value": "Sorry, I don't understand."},
                },
                "raw_output": "Sorry, I don't understand.",
            }
        )

    def _get_clarify_question_then_consecutive_actions(
        self, simbot_game_metadata_dir: Path, starting_turn_idx: int, num_actions: int
    ) -> list[SimBotSessionTurn]:
        turns: list[SimBotSessionTurn] = []

        for turn_idx in range(num_actions):
            # Include clarify question turn if turn idx is 0
            if turn_idx == 0:
                turns.append(
                    self._get_clarification_question_turn(
                        simbot_game_metadata_dir, starting_turn_idx + turn_idx
                    )
                )
                continue

            if turn_idx > 0 and turns[turn_idx - 1].is_clarify_intent:
                turns.append(
                    self._get_look_around_turn(
                        simbot_game_metadata_dir,
                        starting_turn_idx + turn_idx,
                        include_speech=True,
                        include_end_of_trajectory=turn_idx == num_actions - 1,
                    )
                )
                continue

            turns.append(
                self._get_look_around_turn(
                    simbot_game_metadata_dir,
                    starting_turn_idx + turn_idx,
                    include_speech=turn_idx == 0,
                    include_end_of_trajectory=turn_idx == num_actions - 1,
                )
            )

        assert len(turns) == num_actions

        return turns


@fixture(scope="session")
def simbot_session_db_turn() -> str:
    # return '{"session_id": "amzn1.echo-api.session.dd7b95cd-bc64-49d1-81ac-57e885160c20_4", "prediction_request_id": "f9644d5f-7745-490e-abca-147b7cda417c", "idx": 1, "timestamp": {"start": "2022-10-04T17:36:52.996641", "end": null}, "current_room": "SmallOffice", "unique_room_names": ["Reception", "MainOffice", "Lab2", "SmallOffice", "Warehouse", "BreakRoom", "Lab1"], "viewpoints": ["MainOffice_6", "Lab1_6", "Warehouse_5", "Reception_4", "BreakRoom_3", "Reception_1", "Warehouse_2", "Lab1_7", "SmallOffice_8", "Reception_6", "MainOffice_7", "Lab2_4", "MainOffice_5", "Warehouse_3", "SmallOffice_1", "BreakRoom_1", "Lab2_8", "MainOffice_2", "Lab2_7", "BreakRoom_6", "Lab2_1", "Warehouse_4", "BreakRoom_7", "SmallOffice_2", "Lab2_3", "Reception_7", "Lab2_2", "BreakRoom_5", "Lab1_1", "BreakRoom_8", "MainOffice_1", "BreakRoom_4", "MainOffice_8", "Lab1_4", "SmallOffice_6", "SmallOffice_3", "Lab1_3", "Lab1_5", "Lab1_2", "SmallOffice_5", "Reception_2", "SmallOffice_4", "Reception_8", "BreakRoom_2", "SmallOffice_7", "Lab2_6", "MainOffice_4", "Reception_3", "MainOffice_3", "Warehouse_1", "Lab2_5", "Lab1_8", "Reception_5"], "speech": {"tokens": [{"value": "pick", "confidence": {"score": 0.85, "bin": "HIGH"}}, {"value": "up", "confidence": {"score": 0.88, "bin": "HIGH"}}, {"value": "ball", "confidence": {"score": 0.802, "bin": "HIGH"}}]}, "auxiliary_metadata_uri": "efs://amzn1.echo-api.session.dd7b95cd-bc64-49d1-81ac-57e885160c20_4/e7c20078863942d5a4a54e76cefa1e0c_metadata.json", "intent": {"type": "<act>", "object_name": null}, "actions": [{"type": "pickup", "status": null, "pickup": {"object": {"colorImageIndex": 1, "mask": "", "name": "Broken Radio"}}}, {"type": "dialog", "status": null, "dialog": {"value": "Ok, what next?", "intent": null}}], "raw_output": "Pickup Broken Radio <frame_token_1>.</s>"}'
    return '{"session_id": "amzn1.echo-api.session.dd7b95cd-bc64-49d1-81ac-57e885160c20_4", "prediction_request_id": "f9644d5f-7745-490e-abca-147b7cda417c", "idx": 1, "timestamp": {"start": "2022-10-04T17:36:52.996641", "end": null}, "current_room": "SmallOffice", "unique_room_names": ["Reception", "MainOffice", "Lab2", "SmallOffice", "Warehouse", "BreakRoom", "Lab1"], "viewpoints": ["MainOffice_6", "Lab1_6", "Warehouse_5", "Reception_4", "BreakRoom_3", "Reception_1", "Warehouse_2", "Lab1_7", "SmallOffice_8", "Reception_6", "MainOffice_7", "Lab2_4", "MainOffice_5", "Warehouse_3", "SmallOffice_1", "BreakRoom_1", "Lab2_8", "MainOffice_2", "Lab2_7", "BreakRoom_6", "Lab2_1", "Warehouse_4", "BreakRoom_7", "SmallOffice_2", "Lab2_3", "Reception_7", "Lab2_2", "BreakRoom_5", "Lab1_1", "BreakRoom_8", "MainOffice_1", "BreakRoom_4", "MainOffice_8", "Lab1_4", "SmallOffice_6", "SmallOffice_3", "Lab1_3", "Lab1_5", "Lab1_2", "SmallOffice_5", "Reception_2", "SmallOffice_4", "Reception_8", "BreakRoom_2", "SmallOffice_7", "Lab2_6", "MainOffice_4", "Reception_3", "MainOffice_3", "Warehouse_1", "Lab2_5", "Lab1_8", "Reception_5"], "speech": {"tokens": [{"value": "pick", "confidence": {"score": 0.85, "bin": "HIGH"}}, {"value": "up", "confidence": {"score": 0.88, "bin": "HIGH"}}, {"value": "ball", "confidence": {"score": 0.802, "bin": "HIGH"}}]}, "auxiliary_metadata_uri": "efs://amzn1.echo-api.session.dd7b95cd-bc64-49d1-81ac-57e885160c20_4/e7c20078863942d5a4a54e76cefa1e0c_metadata.json", "intent": {"type": "<act>", "object_name": null}, "actions": [{"type": "pickup", "status": null, "pickup": {"object": {"colorImageIndex": 1, "mask": null, "name": "Broken Radio"}}}, {"type": "dialog", "status": null, "dialog": {"value": "Ok, what next?", "intent": null}}], "raw_output": "Pickup Broken Radio <frame_token_1>.</s>"}'
