from enum import Enum

from pydantic import BaseModel, Field

from emma_experience_hub.constants.alexa import ALEXA_WAKE_WORDS
from emma_experience_hub.datamodels.simbot.payloads.payload import SimBotPayload


class SimBotSpeechRecognitionConfidenceBin(Enum):
    """Bins for the confidence levels from the ASR output."""

    low = "LOW"
    medium = "MEDIUM"
    high = "HIGH"


class SimBotSpeechRecognitionConfidence(BaseModel):
    """Confidence scores for the speech recognition sensor."""

    score: float = Field(..., ge=0, le=1)
    bin: SimBotSpeechRecognitionConfidenceBin


class SimBotSpeechRecognitionToken(BaseModel):
    """Predicted tokens from the speech recognition sensor."""

    value: str  # noqa: WPS110
    confidence: SimBotSpeechRecognitionConfidence

    @property
    def is_wake_word(self) -> bool:
        """Returns True if the word is used by Alexa as a wake word."""
        return self.value in ALEXA_WAKE_WORDS


class SimBotSpeechRecognitionPayload(SimBotPayload):
    """Soeech Recognition action from the sensors."""

    _token_delimiter: str = " "

    tokens: list[SimBotSpeechRecognitionToken]

    @property
    def utterance(self) -> str:
        """Get the most likely utterance from all the tokens."""
        all_tokens = (
            token.value for token in self.tokens[self._get_num_wake_words_in_utterance() :]
        )
        return self._token_delimiter.join(all_tokens)

    @property
    def all_confidence_scores(self) -> list[float]:
        """Get all the confidence scores from all the tokens."""
        return [token.confidence.score for token in self.tokens]

    def _get_num_wake_words_in_utterance(self) -> int:
        """Get the number of wake words at the start of the utterance."""
        num_wake_words_in_utterance = 0
        for token in self.tokens:
            if token.is_wake_word:
                num_wake_words_in_utterance += 1
            else:
                break

        return num_wake_words_in_utterance
