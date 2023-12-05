from contextlib import suppress
from typing import Optional

from loguru import logger

from emma_experience_hub.functions.simbot import (
    SimBotSceneObjectTokens,
    extract_index_from_special_token,
)
from emma_experience_hub.parsers.parser import Parser


class SimBotVisualGroundingOutputParser(Parser[list[str], Optional[SimBotSceneObjectTokens]]):
    """Parse the model output into the deconstructed action."""

    def __call__(self, model_output: list[str]) -> Optional[SimBotSceneObjectTokens]:
        """Convert the raw model output into a deconstructed action that we can use."""
        logger.debug(f"Raw model output: `{model_output}`")

        if not model_output:
            logger.info("Model was not able to find the object.")
            return None

        if len(model_output) > 1:
            logger.info("Model found more than one possible object.")

        # Iterate over all the model outputs until one is parsed
        for raw_output in model_output:
            with suppress(IndexError):
                return self._convert_output_to_scene_object_tokens(raw_output)

        logger.warning(
            "None of the returned model outputs were able to be parsed. Returning `None` to treat as if the model did not find anything."
        )
        return None

    def _convert_output_to_scene_object_tokens(self, raw_output: str) -> SimBotSceneObjectTokens:
        """Convert the model raw output into its scene object tokens.

        Each raw output from the model is in the form `<frame_token_x> <vis_token_y>`.
        """
        special_tokens = raw_output.strip().split(" ")

        if len(special_tokens) != 2:
            logger.warning(
                f"The raw output (`{raw_output}`) was not split into 2 special tokens. We are going to try and parse the tokens using the first two tokens only."
            )

        return SimBotSceneObjectTokens(
            frame_index=extract_index_from_special_token(special_tokens[0]),
            object_index=extract_index_from_special_token(special_tokens[1]),
        )
