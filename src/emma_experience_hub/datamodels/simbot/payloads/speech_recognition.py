from pydantic import BaseModel

from emma_experience_hub.datamodels.simbot.payloads.payload import SimBotPayload


class SimBotSpeechRecognitionToken(BaseModel):
    """Predicted tokens from the speech recognition sensor."""

    value: str  # noqa: WPS110


class SimBotSpeechRecognitionPayload(SimBotPayload):
    """Soeech Recognition action from the sensors."""

    _token_delimiter: str = " "

    tokens: list[SimBotSpeechRecognitionToken]

    @property
    def utterance(self) -> str:
        """Get the most likely utterance from all the tokens."""
        all_tokens = (token.value for token in self.tokens)
        return self._token_delimiter.join(all_tokens)
