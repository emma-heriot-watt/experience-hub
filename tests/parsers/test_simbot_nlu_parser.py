from pytest_cases import fixture, parametrize_with_cases

from emma_experience_hub.datamodels.simbot import SimBotAction, SimBotIntent, SimBotIntentType
from emma_experience_hub.parsers.simbot import SimBotNLUOutputParser


@fixture(scope="module")
def intent_type_delimiter() -> str:
    return " "


class DecodedNLUOutputs:
    """Various cases to ensure the SimBot trajectories are parsed correctly."""

    def case_act(self) -> tuple[str, SimBotIntent]:
        return "<act>", SimBotIntent(type=SimBotIntentType.instruction)

    def case_clarify_direction(self) -> tuple[str, SimBotIntent]:
        return "<clarify><direction> mug", SimBotIntent(
            type=SimBotIntentType.clarify_direction, object_name="mug"
        )

    def case_clarify_disambiguation(self) -> tuple[str, SimBotIntent]:
        return "<clarify><disambiguation> cup", SimBotIntent(
            type=SimBotIntentType.clarify_disambiguation, object_name="cup"
        )

    def case_clarify_location(self) -> tuple[str, SimBotIntent]:
        return "<clarify><location> cup", SimBotIntent(
            type=SimBotIntentType.clarify_location, object_name="cup"
        )


@parametrize_with_cases("decoded_actions,expected_output", cases=DecodedNLUOutputs)
def test_decoded_action_trajectories_are_converted_properly(
    decoded_actions: str, expected_output: SimBotAction, intent_type_delimiter: str
) -> None:
    trajectory_parser = SimBotNLUOutputParser(intent_type_delimiter=intent_type_delimiter)
    parsed_trajectory = trajectory_parser(decoded_actions)

    assert parsed_trajectory == expected_output
