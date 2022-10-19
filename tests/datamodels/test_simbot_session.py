import pytest
from pytest_cases import parametrize_with_cases

from emma_experience_hub.datamodels.simbot import (
    SimBotActionType,
    SimBotSession,
    SimBotSessionTurn,
)
from tests.fixtures.simbot_api_requests import SimBotSessionCases


def test_session_turn_parses_from_dynamo_db_output(simbot_session_db_turn: str) -> None:
    parsed_turn = SimBotSessionTurn.parse_raw(simbot_session_db_turn)

    assert parsed_turn


@parametrize_with_cases("session,expected_num_turns", cases=SimBotSessionCases)
def test_get_the_correct_turns_since_local_state_reset(
    session: SimBotSession, expected_num_turns: int
) -> None:
    turns = session.get_turns_since_local_state_reset()

    assert len(turns) == expected_num_turns
    assert turns == session.turns[-expected_num_turns:]


# @pytest.mark.slow
# @parametrize_with_cases("session,expected_num_turns", cases=SimBotSessionCases)
# def test_all_provided_turns_since_local_state_reset_are_actionable(
#     session: SimBotSession, expected_num_turns: int
# ) -> None:
#     turns = session.get_turns_since_local_state_reset()

#     assert len(turns) == expected_num_turns
#     assert turns == session.turns[-expected_num_turns:]

#     assert all(turn.intent.type.is_actionable for turn in turns if turn.intent is not None)


@parametrize_with_cases("session,expected_num_turns", cases=SimBotSessionCases)
def test_turns_with_end_of_trajectory_tokens_include_dialog(
    session: SimBotSession, expected_num_turns: int
) -> None:
    turns_with_end_of_trajectory_tokens = [
        turn for turn in session.turns if turn.output_contains_end_of_trajectory_token
    ]

    if not turns_with_end_of_trajectory_tokens:
        pytest.skip("Session does not contain turns with end of trajectory tokens")

    for turn in turns_with_end_of_trajectory_tokens:
        if turn.actions:
            assert turn.actions[-1].type == SimBotActionType.Dialog
