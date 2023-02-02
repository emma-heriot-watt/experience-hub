from collections import Counter

from pytest_cases import fixture

from emma_experience_hub.datamodels.simbot import SimBotFeedbackState
from emma_experience_hub.parsers.simbot.feedback_from_session_context import (
    SimBotFeedbackFromSessionStateParser,
)


MIN_RULE_ID = 2


@fixture(scope="module")
def rule_parser() -> SimBotFeedbackFromSessionStateParser:
    """Instantiate the rule parser."""
    return SimBotFeedbackFromSessionStateParser.from_rules_csv()


def test_all_rules_are_valid(rule_parser: SimBotFeedbackFromSessionStateParser) -> None:
    assert rule_parser._rules


def test_ensure_no_rule_id_is_below_minumum(
    rule_parser: SimBotFeedbackFromSessionStateParser,
) -> None:
    all_rule_ids = [rule.id for rule in rule_parser._rules]

    assert min(all_rule_ids) == MIN_RULE_ID


def test_all_rule_ids_are_unique(rule_parser: SimBotFeedbackFromSessionStateParser) -> None:
    ids_counter = Counter([rule.id for rule in rule_parser._rules])

    # Get IDs which appear more than once in the list
    repeated_ids = [rule_id for (rule_id, count) in ids_counter.items() if count > 1]

    # Assert that the list of repeated IDs IS empty
    assert not repeated_ids


def test_rule_ids_are_consecutive(rule_parser: SimBotFeedbackFromSessionStateParser) -> None:
    all_rule_ids = [rule.id for rule in rule_parser._rules]
    all_rule_ids.sort()

    # Create a simple list of all numbers from 0 to the total number of rules
    consecutive_numbers = range(MIN_RULE_ID, len(all_rule_ids))

    for actual_rule_id, expected_rule_id in zip(all_rule_ids, consecutive_numbers):
        assert (
            actual_rule_id == expected_rule_id
        ), f"Rule {actual_rule_id} should be {expected_rule_id}"


def test_response_slots_in_all_rules(rule_parser: SimBotFeedbackFromSessionStateParser) -> None:
    """Test that all slots in resposes are included in the rule."""
    rules_and_slots = [
        (rule.rule.text, rule.slot_names) for rule in rule_parser._rules if rule.slot_names
    ]
    for rule_text, slots in rules_and_slots:
        rule_words = rule_text.split()
        assert all([slot_name in rule_words for slot_name in slots])


def test_all_response_slots_are_validated_by_rules(
    rule_parser: SimBotFeedbackFromSessionStateParser,
) -> None:
    """Test that all slots in resposes are included in the rule."""
    rules_and_slots = [
        (rule.rule.text, rule.slot_names) for rule in rule_parser._rules if rule.slot_names
    ]
    for rule_text, slots in rules_and_slots:
        assert all([f"{slot_name} != null" in rule_text for slot_name in slots])


def test_all_rule_symbols_in_state(rule_parser: SimBotFeedbackFromSessionStateParser) -> None:
    """Test that all rule symbols appear in the state."""
    state_fields = set(SimBotFeedbackState.__fields__.keys())
    for rule in rule_parser._rules:
        # Get the rule symbols
        symbols = rule.rule.context.symbols
        assert symbols.issubset(state_fields)


# @given(session=simbot_session())
# def test_can_get_rule_from_example_state(
#     rule_parser: SimBotFeedbackFromSessionStateParser, session: SimBotSession
# ) -> None:
#     feedback_state = session.to_feedback_state()
#     rule = rule_parser(feedback_state)

#     assert rule is not None
