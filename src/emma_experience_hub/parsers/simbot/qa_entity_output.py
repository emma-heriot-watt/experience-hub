from typing import Any, Optional, cast

from loguru import logger

from emma_experience_hub.datamodels.simbot import (
    SimBotAnyUserIntentType,
    SimBotIntent,
    SimBotIntentType,
    SimBotUserQAType,
)
from emma_experience_hub.parsers.parser import Parser


class SimBotQAEntityParser(
    Parser[dict[str, Any], Optional[SimBotIntent[SimBotAnyUserIntentType]]]
):
    """Parse the output of the QA client."""

    def __init__(self, instruction_intent: str = "instruct") -> None:
        self._instruction_intent = instruction_intent

    def __call__(
        self, intent_entity_response: dict[str, Any]
    ) -> Optional[SimBotIntent[SimBotAnyUserIntentType]]:
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
        # check for incomplete find, goto
        selected_entity = None
        intent_requires_entity = (
            qa_intent_str in {"ask_about_appearance", "ask_about_affordance", "ask_about_location"}
            and qa_entities_response
        )
        if intent_requires_entity:
            try:
                selected_entity = self._extract_diet_entities_for_object_qa(qa_entities_response)
            except KeyError:
                logger.warning(f"Unable extract entities from : {qa_entities_response}")
                return None

        # By the time we get here, the intents _should_ convert to the right form.
        try:
            intent_type = SimBotIntentType[qa_intent_str]
        except KeyError:
            logger.warning(f"Failed to parse the intent from the string `{qa_intent_str}`")
            return None

        intent_type = cast(SimBotUserQAType, intent_type)
        return SimBotIntent(type=intent_type, entity=selected_entity)

    def _extract_diet_entities_for_object_qa(self, entities: list[Any]) -> Optional[str]:
        diet_entities = [
            entity["value"] for entity in entities if entity["extractor"] == "DIETClassifier"
        ]
        if len(diet_entities) == 1:  # if there are multiple diet entities,qa can not handle this
            return diet_entities[0]

        return None
