import itertools
import random
from collections.abc import Iterator
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import Optional

from loguru import logger
from opentelemetry import trace

from emma_experience_hub.constants.simbot import get_feedback_rules
from emma_experience_hub.datamodels.simbot import SimBotFeedbackRule, SimBotFeedbackState
from emma_experience_hub.parsers.parser import Parser


tracer = trace.get_tracer(__name__)


class SimBotFeedbackFromSessionStateParser(Parser[SimBotFeedbackState, SimBotFeedbackRule]):
    """Get the best response for the current session feedback state."""

    _default_rule_id: int = 0

    def __init__(
        self, rules: list[SimBotFeedbackRule], _max_workers: Optional[int] = None
    ) -> None:
        self._rules = rules
        self._max_workers = _max_workers

    def __call__(self, session_state: SimBotFeedbackState) -> SimBotFeedbackRule:
        """Get the best feedback from the current context."""
        candidate_rules = self._get_all_compatible_rules(session_state)
        selected_rule = self._select_feedback_rule(candidate_rules, session_state.used_rule_ids)
        return selected_rule

    @classmethod
    def from_rules_csv(cls) -> "SimBotFeedbackFromSessionStateParser":
        """Instantiate the class from the rules CSV file."""
        rule_data = get_feedback_rules()

        with ThreadPoolExecutor() as executor:
            rules = list(executor.map(SimBotFeedbackRule.from_raw, rule_data))

        logger.debug(f"Loaded {len(rules)} feedback rules.")
        return cls(rules=rules)

    @tracer.start_as_current_span("Get compatible rules")
    def _get_all_compatible_rules(self, state: SimBotFeedbackState) -> list[SimBotFeedbackRule]:
        """Get all of the rules which are compatible with the current state."""
        # Store all the compatible rules with the given query
        compatible_rules: list[SimBotFeedbackRule] = []

        # Try filter rules to remove any that are clearly unneeded
        filtered_rules = self._filter_rules(state)

        # Convert the session state to a dictionary we can iterate over.
        query_dict = state.to_query()

        # Use multithreading to evaluate every single rule as fast as possible
        with ThreadPoolExecutor(self._max_workers) as executor:
            future_to_rule: dict[Future[bool], SimBotFeedbackRule] = {
                executor.submit(rule.is_query_suitable, query_dict): rule
                for rule in filtered_rules
            }

            for future in as_completed(future_to_rule):
                rule = future_to_rule[future]

                try:
                    future.result()
                except Exception:
                    logger.exception(f"Failed to check whether rule {rule.id} is compatible")
                else:
                    if future.result():
                        compatible_rules.append(rule)  # noqa: WPS220

        logger.debug(f"Got {len(compatible_rules)} matching feedback rules.")
        return compatible_rules

    def _filter_rules(self, state: SimBotFeedbackState) -> Iterator[SimBotFeedbackRule]:
        """Filter the rules if possible to ensure that certain rules are returned."""
        filtered_rules = iter(self._rules)

        if state.require_lightweight_dialog:
            filtered_rules = (rule for rule in self._rules if rule.is_lightweight_dialog)

        return filtered_rules

    @tracer.start_as_current_span("Select feedback rule")
    def _select_feedback_rule(
        self, candidates: list[SimBotFeedbackRule], used_rule_ids: list[int]
    ) -> SimBotFeedbackRule:
        """Select the highest-scoring rule from the set of rules."""
        # Try to filter out any rules that have already been used
        valid_candidates = [rule for rule in candidates if rule.id not in used_rule_ids]

        if not valid_candidates:
            logger.warning("No unused candidate rules! Will need to reuse a response.")
            valid_candidates = candidates

        # Group all the rules by their scores
        sorted_candidates = sorted(valid_candidates, key=lambda x: x.score, reverse=True)
        grouped_candidates = itertools.groupby(sorted_candidates, key=lambda x: x.score)

        try:
            # Get the group of rules with the highest score
            highest_scoring_rules = list(next(grouped_candidates)[1])
            # Choose one of the rules from the highest-scoring set
            selected_rule = random.choice(highest_scoring_rules)
        except (StopIteration, IndexError):
            # If the list of rules is empty for some reason, then just return the default rule
            selected_rule = self._rules[self._default_rule_id]
            logger.error(f"[NLG] No rules to choose, therefore using default {selected_rule}")

        logger.debug(f"[NLG] Selected rule {selected_rule}")
        return selected_rule
