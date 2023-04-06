from typing import Optional

from pydantic import BaseModel

from emma_common.datamodels import SpeakerRole
from emma_experience_hub.datamodels.simbot.payloads import SimBotSpeechRecognitionPayload


class SimBotUtterance(BaseModel):
    """User utterance."""

    utterance: str
    from_utterance_queue: bool = False
    role: SpeakerRole = SpeakerRole.user


class SimBotUserSpeech(BaseModel):
    """Utterance from the user or self-generated instruction for the SimBot challenge."""

    original_utterance: SimBotUtterance
    modified_utterance: Optional[SimBotUtterance] = None

    @classmethod
    def from_speech_recognition_payload(
        cls, speech_recognition_payload: SimBotSpeechRecognitionPayload
    ) -> "SimBotUserSpeech":
        """Convert the speech recognition payload into a simpler datamodel."""
        return cls(
            original_utterance=SimBotUtterance(utterance=speech_recognition_payload.utterance),
        )

    @classmethod
    def update_user_utterance(
        cls,
        utterance: str,
        original_utterance: Optional[SimBotUtterance] = None,
        from_utterance_queue: bool = False,
        role: SpeakerRole = SpeakerRole.user,
    ) -> "SimBotUserSpeech":
        """Update the user utterance."""
        new_utterance = SimBotUtterance(
            utterance=utterance, role=role, from_utterance_queue=from_utterance_queue
        )
        # If there wasn't a previous original utterance, consider the new utterance as original
        if original_utterance is None:
            return cls(
                original_utterance=new_utterance,
                modified_utterance=new_utterance,
            )
        return cls(original_utterance=original_utterance, modified_utterance=new_utterance)

    @property
    def utterance(self) -> str:
        """Get the speech utterance."""
        if self.modified_utterance is not None:
            return self.modified_utterance.utterance
        return self.original_utterance.utterance

    @property
    def role(self) -> SpeakerRole:
        """Get the speaker role."""
        if self.modified_utterance is not None:
            return self.modified_utterance.role
        return self.original_utterance.role

    @property
    def from_utterance_queue(self) -> bool:
        """Is the utterance from the queue?"""
        if self.modified_utterance is not None:
            return self.modified_utterance.from_utterance_queue
        return self.original_utterance.from_utterance_queue
