from pydantic import BaseModel

from emma_common.datamodels import SpeakerRole
from emma_experience_hub.datamodels.simbot.payloads import SimBotSpeechRecognitionPayload


class SimBotUserSpeech(BaseModel):
    """Utterance from the user for the SimBot challenge."""

    utterance: str
    from_utterance_queue: bool = False
    role: SpeakerRole = SpeakerRole.user

    @classmethod
    def from_speech_recognition_payload(
        cls, speech_recognition_payload: SimBotSpeechRecognitionPayload
    ) -> "SimBotUserSpeech":
        """Convert the speech recognition payload into a simpler datamodel."""
        return cls(utterance=speech_recognition_payload.utterance)
