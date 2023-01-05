from collections import Counter
from contextlib import suppress

from loguru import logger
from pytest_cases import fixture
from rule_engine import Rule

from emma_experience_hub.datamodels.simbot import SimBotFeedbackState
from emma_experience_hub.parsers.simbot.feedback_from_session_context import (
    SimBotFeedbackFromSessionStateParser,
)


logger.level("ERROR")

rules = {
    1: Rule('user_intent == "low_asr_confidence"'),
    2: Rule('user_intent == "low_asr_confidence" and low_asr_intent_count == 1'),
    3: Rule(
        'user_intent == "low_asr_confidence" and low_asr_intent_count == 1 or low_asr_intent_count == 5'
    ),
    4: Rule('user_intent == "out_of_domain"'),
}


def test_simple_response_generation_works() -> None:
    example_context = {"user_intent": "low_asr_confidence", "low_asr_intent_count": 1}
    valid_rule_keys = []
    for rule_id, rule in rules.items():
        with suppress(Exception):
            if rule.matches(example_context):
                valid_rule_keys.append(rule_id)

    assert valid_rule_keys


@fixture(scope="module")
def rule_parser() -> SimBotFeedbackFromSessionStateParser:
    """Instantiate the rule parser."""
    return SimBotFeedbackFromSessionStateParser.from_rules_csv()


def test_all_rules_are_valid(rule_parser: SimBotFeedbackFromSessionStateParser) -> None:
    assert rule_parser._rules


def test_all_rule_ids_are_unique(rule_parser: SimBotFeedbackFromSessionStateParser) -> None:
    ids_counter = Counter([rule.id for rule in rule_parser._rules])

    # Get IDs which appear more than once in the list
    repeated_ids = [rule_id for (rule_id, count) in ids_counter.items() if count > 1]

    # Assert that the list of repeated IDs IS empty
    assert not repeated_ids


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
