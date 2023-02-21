from typing import Any, Optional, cast

from loguru import logger

from emma_experience_hub.datamodels.simbot import SimBotIntentType, SimBotUserQAType
from emma_experience_hub.parsers.parser import Parser


class SimBotQAOutputParser(Parser[dict[str, Any], Optional[SimBotUserQAType]]):
    """Parse the output of the QA client."""

    def __init__(self, instruction_intent: str = "instruct") -> None:
        self._instruction_intent = instruction_intent

    def __call__(self, intent_entity_response: dict[str, Any]) -> Optional[SimBotUserQAType]:
        """Parses the intent from rasa intent entity extraction."""
        logger.debug(f"SimBotQA output: `{intent_entity_response}`")

        # Get the intent from the response
        try:
            qa_intent_str: str = intent_entity_response["intent"]["name"]
        except KeyError:
            logger.warning(
                f"Intent key does not exist within the response: {intent_entity_response}"
            )
            return None

        # If it is a fallback or an instruction, ignore
        if qa_intent_str == "nlu_fallback" or qa_intent_str.startswith(self._instruction_intent):
            return None

        # By the time we get here, the intents _should_ convert to the right form.
        try:
            intent_type = SimBotIntentType[qa_intent_str]
        except KeyError:
            logger.warning(f"Failed to parse the intent from the string `{qa_intent_str}`")
            return None

        intent_type = cast(SimBotUserQAType, intent_type)

        return intent_type
