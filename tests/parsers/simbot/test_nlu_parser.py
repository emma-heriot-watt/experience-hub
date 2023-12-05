from pytest_cases import fixture, param_fixture, parametrize_with_cases

from emma_experience_hub.datamodels.simbot import (
    SimBotAction,
    SimBotCRIntentType,
    SimBotIntent,
    SimBotIntentType,
)
from emma_experience_hub.parsers.simbot import SimBotCROutputParser


@fixture(scope="session")
def intent_type_delimiter() -> str:
    return " "


should_include_entity = param_fixture(
    "should_include_entity", [True, False], ids=["with_entity", "without_entity"]
)


class DecodedCROutputs:
    """Various cases to ensure the various intents are parsed correctly."""

    _entity: str = "mug"

    def case_act(self) -> tuple[str, SimBotIntent[SimBotCRIntentType]]:
        return "<act><one_match>", SimBotIntent[SimBotCRIntentType](
            type=SimBotIntentType.act_one_match
        )

    def case_search(self) -> tuple[str, SimBotIntent[SimBotCRIntentType]]:
        return "<search>", SimBotIntent[SimBotCRIntentType](type=SimBotIntentType.search)

    def case_act_too_many_matches(
        self, should_include_entity: bool
    ) -> tuple[str, SimBotIntent[SimBotCRIntentType]]:
        output = "<act><too_many_matches>"
        if should_include_entity:
            output = f"{output} {self._entity}"

        intent = SimBotIntent[SimBotCRIntentType](
            type=SimBotIntentType.act_too_many_matches,
            entity=self._entity if should_include_entity else None,
        )

        return output, intent

    def case_act_no_match(
        self, should_include_entity: bool
    ) -> tuple[str, SimBotIntent[SimBotCRIntentType]]:
        output = "<act><no_match>"
        if should_include_entity:
            output = f"{output} {self._entity}"

        intent = SimBotIntent[SimBotCRIntentType](
            type=SimBotIntentType.act_no_match,
            entity=self._entity if should_include_entity else None,
        )

        return output, intent


@parametrize_with_cases("decoded_actions,expected_output", cases=DecodedCROutputs)
def test_parser_decodes_cr_output(
    decoded_actions: str, expected_output: SimBotAction, intent_type_delimiter: str
) -> None:
    trajectory_parser = SimBotCROutputParser(intent_type_delimiter=intent_type_delimiter)
    parsed_trajectory = trajectory_parser(decoded_actions)

    assert parsed_trajectory == expected_output
