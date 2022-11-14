from pytest_cases import fixture, param_fixture, parametrize_with_cases

from emma_experience_hub.datamodels.simbot import SimBotAction, SimBotIntent, SimBotIntentType
from emma_experience_hub.parsers.simbot import SimBotNLUOutputParser


@fixture(scope="session")
def intent_type_delimiter() -> str:
    return " "


should_include_entity = param_fixture(
    "should_include_entity", [True, False], ids=["with_entity", "without_entity"]
)


class DecodedNLUOutputs:
    """Various cases to ensure the various intents are parsed correctly."""

    _entity: str = "mug"

    def case_act(self) -> tuple[str, SimBotIntent]:
        return "<act>", SimBotIntent(type=SimBotIntentType.act)

    def case_clarify_direction(self, should_include_entity: bool) -> tuple[str, SimBotIntent]:
        output = "<clarify><direction>"
        if should_include_entity:
            output = f"{output} {self._entity}"

        intent = SimBotIntent(
            type=SimBotIntentType.clarify_direction,
            entity=self._entity if should_include_entity else None,
        )

        return output, intent

    def case_clarify_disambiguation(self, should_include_entity: bool) -> tuple[str, SimBotIntent]:
        output = "<clarify><disambiguation>"
        if should_include_entity:
            output = f"{output} {self._entity}"

        intent = SimBotIntent(
            type=SimBotIntentType.clarify_disambiguation,
            entity=self._entity if should_include_entity else None,
        )

        return output, intent

    def case_clarify_location(self, should_include_entity: bool) -> tuple[str, SimBotIntent]:
        output = "<clarify><location>"
        if should_include_entity:
            output = f"{output} {self._entity}"

        intent = SimBotIntent(
            type=SimBotIntentType.clarify_location,
            entity=self._entity if should_include_entity else None,
        )

        return output, intent

    def case_clarify_description(self, should_include_entity: bool) -> tuple[str, SimBotIntent]:
        output = "<clarify><description>"
        if should_include_entity:
            output = f"{output} {self._entity}"

        intent = SimBotIntent(
            type=SimBotIntentType.clarify_description,
            entity=self._entity if should_include_entity else None,
        )

        return output, intent


@parametrize_with_cases("decoded_actions,expected_output", cases=DecodedNLUOutputs)
def test_parser_decodes_nlu_output(
    decoded_actions: str, expected_output: SimBotAction, intent_type_delimiter: str
) -> None:
    trajectory_parser = SimBotNLUOutputParser(intent_type_delimiter=intent_type_delimiter)
    parsed_trajectory = trajectory_parser(decoded_actions)

    assert parsed_trajectory == expected_output
