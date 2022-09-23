from enum import Enum

from pydantic import BaseModel, Field


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


class SimBotSpeechRecognitionPayload(BaseModel):
    """Soeech Recognition action from the sensors."""

    _token_delimiter: str = " "

    tokens: list[SimBotSpeechRecognitionToken]

    @property
    def utterance(self) -> str:
        """Get the most likely utterance from all the tokens."""
        all_tokens = (token.value for token in self.tokens)
        return self._token_delimiter.join(all_tokens)
