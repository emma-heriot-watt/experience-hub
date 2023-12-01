import re
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
        self._incomplete_utterance_regex_pattern = self._regex_patterns_map()

    def __call__(self, intent_entity_response: dict[str, Any]) -> Optional[SimBotUserQAType]:
        """Parses the intent from rasa intent entity extraction."""
        logger.debug(f"SimBotQA output: `{intent_entity_response}`")

        # Get the intent from the response
        try:  # noqa: WPS229
            utterance = intent_entity_response["text"]
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
                utterance=utterance, intent=qa_intent_str, entities=qa_entities_response
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

    def _process_intent(self, utterance: str, intent: str, entities: list[Any]) -> str:
        # if rasa model found an entity or there was no regex match for incomplete utterance
        if entities or not self._is_regex_match_for_incomplete_utterance(utterance):
            return intent
        # if the utterance has 5 or more tokens, it will not be filtered. Long sequences may contain un accounted valid instruction
        if len(utterance.split(" ")) > 4:
            return intent

        if intent == "instruct_find":
            intent = "incomplete_utterance_find"

        if intent == "instruct_pick":
            intent = "incomplete_utterance_pick"

        if intent == "instruct_place":
            intent = "incomplete_utterance_place"

        if intent == "instruct_goto":
            intent = "incomplete_utterance_goto"

        return intent

    def _is_regex_match_for_incomplete_utterance(self, utterance: str) -> bool:
        if re.search(self._incomplete_utterance_regex_pattern, utterance):
            logger.debug(f"found incomplete regex match for the utterance: {utterance}")
            return True
        logger.debug(f"No incomplete regex match for the utterance: {utterance}")
        return False

    def _regex_patterns_map(self) -> str:
        verbs = [
            "find",
            "search",
            "search for",
            "look for",
            "locate",
            "pick",
            "pick up",
            "take",
            "get",
            "take out",
            "take off",
            "grab",
            "retrieve",
            "place",
            "put",
            "deliver",
            "leave",
            "set",
            "insert",
            "stack",
            "goto",
            "go to",
            "get to",
            "move to",
            "move towards",
        ]
        patterns = [rf"\S?{verb}( the| a| an)?$" for verb in verbs]
        combined_pattern = "|".join(patterns)
        final_regex = f"({combined_pattern})"
        return final_regex
