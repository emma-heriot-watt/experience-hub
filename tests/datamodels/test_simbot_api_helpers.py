from pytest_cases import parametrize_with_cases

from emma_experience_hub.datamodels.simbot import (
    SimBotSession,
    update_simbot_intents_for_emma_policy,
)
from tests.fixtures.simbot_api_requests import SimBotSessionCases


@parametrize_with_cases("session,expected_num_turns", cases=SimBotSessionCases)
def test_utterance_intents_are_updated_correctly_for_policy_api(
    session: SimBotSession, expected_num_turns: int
) -> None:
    dialogue_history = session.get_dialogue_history(session.turns)
    updated_dialogue_history = update_simbot_intents_for_emma_policy(dialogue_history)

    for idx, utterance in enumerate(updated_dialogue_history):
        # Ensure an intent exists
        assert utterance.intent

        # Ensure that the intent is one of the following that are supported by policy
        # assert utterance.intent in {"instruction", "clarify_question", "clarify_answer"}

        # Ensure that the clarify answer is from the user
        if utterance.role == "user":
            assert utterance.intent != "clarify_question"

        # Ensure that the clarify question is from the agent
        if utterance.role == "agent":
            assert utterance.intent != "clarify_answer"

        if utterance.intent == "clarify_question":
            # Make sure the utterance following the clarify question is a clarify answer
            assert updated_dialogue_history[idx + 1].intent == "clarify_answer"

            # Make sure the user is the one that provides the clarify answer
            assert updated_dialogue_history[idx + 1].role == "user"
