from emma_experience_hub.api.clients.simbot_session_db import (
    SimBotSessionDbClient,
    SimBotSessionTurn,
)


def test_client_can_create_session_turn(
    dynamo_db_client: SimBotSessionDbClient, session_turn: SimBotSessionTurn
) -> None:

    dynamo_db_client.put_session_turn(session_turn)
