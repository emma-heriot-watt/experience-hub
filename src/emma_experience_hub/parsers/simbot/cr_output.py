from typing import cast

from loguru import logger

from emma_experience_hub.datamodels.simbot import (
    SimBotCRIntentType,
    SimBotIntent,
    SimBotIntentType,
)
from emma_experience_hub.parsers.parser import NeuralParser


class SimBotCROutputParser(NeuralParser[SimBotIntent[SimBotCRIntentType]]):
    """Convert the output from the SimBot CR module to a SimBot intent."""

    def __init__(self, intent_type_delimiter: str) -> None:
        self._intent_type_delimiter = intent_type_delimiter

    def __call__(self, output_text: str) -> SimBotIntent[SimBotCRIntentType]:
        """Parses the intent generated by the CR component.

        The model is trained with the following templates:
            - <act><one_match>
            - <act><no_match> object_name
            - <act><too_many_matches> object_name
            - <act><missing_inventory> object_name
            - <search>
        """
        logger.debug(f"CR output text: `{output_text}`")

        # Split the raw output text by the given delimiter. We assume it's a " " separating the
        # special tokens and the object_name.
        split_parts = output_text.split(self._intent_type_delimiter)

        # Get the intent type from the left-side of the template.
        intent_type = SimBotIntentType(split_parts[0])
        intent_type = cast(SimBotCRIntentType, intent_type)

        # If it exists, get the object name from the right-side of the template
        object_name = " ".join(split_parts[1:]) if len(split_parts) > 1 else None

        return SimBotIntent(type=intent_type, entity=object_name)