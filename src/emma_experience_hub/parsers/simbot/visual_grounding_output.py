from loguru import logger

from emma_experience_hub.parsers.parser import NeuralParser
from emma_experience_hub.parsers.simbot.functions import SimBotSceneObjectTokens


class SimBotVisualGroundingOutputParser(NeuralParser[SimBotSceneObjectTokens]):
    """Parse the model output into the deconstructed action."""

    def __init__(self, action_delimiter: str, eos_token: str) -> None:
        self._eos_token = eos_token
        self._action_delimiter = action_delimiter

    def __call__(self, model_output: str) -> SimBotSceneObjectTokens:
        """Convert the raw model output into a deconstructed action that we can use."""
        logger.debug(f"Raw model output: `{model_output}`")

        raise NotImplementedError
