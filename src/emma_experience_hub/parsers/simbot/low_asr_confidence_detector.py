from loguru import logger

from emma_experience_hub.datamodels.simbot.payloads import SimBotSpeechRecognitionPayload
from emma_experience_hub.parsers.parser import Parser


class SimBotLowASRConfidenceDetector(Parser[SimBotSpeechRecognitionPayload, bool]):
    """Detect low confidence in the ASR output so we do not try to act on unknown inputs."""

    def __init__(self, avg_confidence_threshold: float = 0.5) -> None:
        self._avg_confidence_threshold = avg_confidence_threshold

    def __call__(self, asr_output: SimBotSpeechRecognitionPayload) -> bool:
        """Determine whether we should accept the ASR output."""
        # If there are no confidence scores for some reason, return False
        if not asr_output.all_confidence_scores:
            logger.warning(
                "There are no confidence scores to average? Why have we recieved an ASR output without confidence scores?",
            )
            return False

        average_confidence_score = self._get_average_confidence_score(
            asr_output.all_confidence_scores
        )
        is_score_above_threshold = average_confidence_score > self._avg_confidence_threshold

        logger.debug(
            f"Avg. confidence score `{average_confidence_score}` > threshold `{self._avg_confidence_threshold}` == `{is_score_above_threshold}`"
        )

        return is_score_above_threshold

    def _get_average_confidence_score(self, all_confidence_scores: list[float]) -> float:
        return sum(all_confidence_scores) / len(all_confidence_scores)
