from emma_experience_hub.datamodels.simbot import SimBotSessionTurn


def test_session_turn_parses_from_dynamo_db_output(simbot_session_db_turn: str) -> None:
    parsed_turn = SimBotSessionTurn.parse_raw(simbot_session_db_turn)

    assert parsed_turn
