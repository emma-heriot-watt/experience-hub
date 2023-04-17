from typing import Any, Optional, cast

from loguru import logger

from emma_experience_hub.datamodels.simbot import SimBotIntentType, SimBotUserQAType
from emma_experience_hub.parsers.parser import Parser


class SimBotQAOutputParser(Parser[dict[str, Any], Optional[SimBotUserQAType]]):
    """Parse the output of the QA client."""

    def __init__(
        self,
        instruction_intent: str = "instruct",
        enable_incomplete_utterances_intent: bool = False,
    ) -> None:
        self._instruction_intent = instruction_intent
        self._enable_incomplete_utterances_intent = enable_incomplete_utterances_intent

    def __call__(self, intent_entity_response: dict[str, Any]) -> Optional[SimBotUserQAType]:
        """Parses the intent from rasa intent entity extraction."""
        logger.debug(f"SimBotQA output: `{intent_entity_response}`")

        # Get the intent from the response
        try:
            qa_intent_str: str = intent_entity_response["intent"]["name"]
            qa_entities_response: list[Any] = intent_entity_response["entities"]
        except KeyError:
            logger.warning(
                f"Intent key does not exist within the response: {intent_entity_response}"
            )
            return None

        # If it is a fallback or an instruction, ignore
        if qa_intent_str == "nlu_fallback":
            return None

        should_process_intent = (
            self._enable_incomplete_utterances_intent
            and qa_intent_str.startswith(self._instruction_intent)
        )
        if should_process_intent:
            processed_intent = self._process_intent(
                intent=qa_intent_str, entities=qa_entities_response
            )
            if processed_intent == qa_intent_str:
                return None
            else:
                qa_intent_str = processed_intent

        # By the time we get here, the intents _should_ convert to the right form.
        try:
            intent_type = SimBotIntentType[qa_intent_str]
        except KeyError:
            logger.warning(f"Failed to parse the intent from the string `{qa_intent_str}`")
            return None

        intent_type = cast(SimBotUserQAType, intent_type)

        return intent_type

    def _process_intent(self, intent: str, entities: list[Any]) -> str:
        # @TODO handle based on the extractor/entity. Reject if it can not be resolved to a known set of entities
        if intent == "instruct_find" and not entities:
            return "incomplete_utterance_find"

        if intent == "instruct_goto" and not entities:
            return "incomplete_utterance_goto"
        return intent
