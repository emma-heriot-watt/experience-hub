from typing import Optional

from loguru import logger
from opentelemetry import trace

from emma_experience_hub.constants.simbot import ACTION_SYNONYMS_FOR_GENERATION, ROOM_SYNONYNMS
from emma_experience_hub.datamodels.simbot import (
    SimBotActionType,
    SimBotDialogAction,
    SimBotFeedbackRule,
    SimBotFeedbackState,
    SimBotSession,
)
from emma_experience_hub.datamodels.simbot.payloads import SimBotDialogPayload
from emma_experience_hub.parsers.simbot.feedback_from_session_context import (
    SimBotFeedbackFromSessionStateParser,
)


tracer = trace.get_tracer(__name__)


class SimBotAgentLanguageGenerationPipeline:
    """Generate language for the agent to say to the user."""

    _default_entity = "object"

    def __init__(self) -> None:
        self._feedback_parser = SimBotFeedbackFromSessionStateParser.from_rules_csv()

    def run(self, session: SimBotSession) -> SimBotDialogAction:
        """Generate an utterance to send back to the user."""
        with tracer.start_as_current_span("Get feedback state"):
            feedback_state = session.to_feedback_state()

        with tracer.start_as_current_span("Choose utterance"):
            matching_rule = self._feedback_parser(feedback_state)

        action = self._generate_dialog_action(matching_rule, feedback_state)

        return action

    def _generate_dialog_action(
        self, rule: SimBotFeedbackRule, feedback_state: SimBotFeedbackState
    ) -> SimBotDialogAction:
        """Generate a dialog action."""
        utterance = self._generate_utterance(rule, feedback_state)

        # Determine the dialog type for the response
        dialog_type = (
            SimBotActionType.LightweightDialog
            if rule.is_lightweight_dialog or feedback_state.utterance_queue_not_empty
            else SimBotActionType.Dialog
        )

        return SimBotDialogAction(
            id=0,
            raw_output=utterance,
            type=dialog_type,
            payload=SimBotDialogPayload(value=utterance, rule_id=rule.id),
        )

    def _generate_utterance(
        self, rule: SimBotFeedbackRule, feedback_state: SimBotFeedbackState
    ) -> str:
        """Generate utterance from the rule and the feedback state."""
        # Build the query dictionary from the feedback state
        query_dict = feedback_state.to_query()
        logger.debug(f"Feedback Query Dict: {query_dict}")

        # Create the slot value pairs for the response
        slot_value_pairs = {
            slot_name: self._process_slot_name(query_dict[slot_name])
            for slot_name in rule.slot_names
        }

        # Build the response itself
        utterance = rule.response.format(**slot_value_pairs)

        logger.debug(f"[NLG] Generated utterance from rule {rule.id}: {utterance}")
        return utterance

    def _process_slot_name(self, entity: Optional[str]) -> str:
        """Return a synonym for the entity name if possible."""
        if not entity:
            return self._default_entity

        action_synonym = ACTION_SYNONYMS_FOR_GENERATION.get(entity, None)

        if action_synonym is not None:
            return action_synonym

        return ROOM_SYNONYNMS.get(entity, entity)
