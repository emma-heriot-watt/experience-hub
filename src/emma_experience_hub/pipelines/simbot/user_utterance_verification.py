from typing import Optional

from loguru import logger

from emma_experience_hub.api.clients import OutOfDomainDetectorClient, ProfanityFilterClient
from emma_experience_hub.datamodels.simbot import (
    SimBotIntentType,
    SimBotInvalidUtteranceIntentType,
)
from emma_experience_hub.datamodels.simbot.payloads import SimBotSpeechRecognitionPayload
from emma_experience_hub.parsers import Parser


class SimBotUserUtteranceVerificationPipeline:
    """Validate the utterance from the user is valid.

    The sole purpose of this pipeline is to check whether the incoming utterance is invalid. If it
    is not invalid, this pipeline does not process anything else and returns `None`.
    """

    def __init__(
        self,
        profanity_filter_client: ProfanityFilterClient,
        out_of_domain_detector_client: OutOfDomainDetectorClient,
        low_asr_confidence_detector: Parser[SimBotSpeechRecognitionPayload, bool],
    ) -> None:
        self._profanity_filter_client = profanity_filter_client
        self._out_of_domain_detector_client = out_of_domain_detector_client
        self._low_asr_confidence_detector = low_asr_confidence_detector

    def run(  # noqa: WPS212
        self, speech_recognition_payload: SimBotSpeechRecognitionPayload
    ) -> Optional[SimBotInvalidUtteranceIntentType]:
        """Check if the utterance is invalid, returning the type if it is invalid."""
        # Check whether or not the utterance contains profanity
        if self._utterance_contains_profanity(speech_recognition_payload):
            logger.debug("Utterance contains profanity.")
            return SimBotIntentType.profanity

        # Check whether ASR confidence is high enough
        if self._utterance_is_low_asr_confidence(speech_recognition_payload):
            logger.debug("ASR confidence is too low; therefore we cannot understand the user.")
            return SimBotIntentType.low_asr_confidence

        # Check if only the wake word exists in the utterance
        if self._utterance_only_contains_wake_word(speech_recognition_payload):
            logger.debug("Utterance only contains wake words.")
            return SimBotIntentType.only_wake_word

        # Check if the utterance is empty
        if self._utterance_is_empty(speech_recognition_payload):
            logger.debug("Utterance is empty and doesn't contain any text.")
            return SimBotIntentType.empty_utterance

        # Check whether or not the utterance is out of domain
        if self._utterance_is_out_of_domain(speech_recognition_payload):
            logger.debug("Utterance is out of domain.")
            return SimBotIntentType.out_of_domain

        # Utterance is not invalid
        return None

    def _utterance_is_low_asr_confidence(
        self, speech_recognition_payload: SimBotSpeechRecognitionPayload
    ) -> bool:
        """Check whether or not the incoming utterance has a low ASR confidence."""
        # If True, then it is ABOVE the threshold and it is NOT low ASR
        return not self._low_asr_confidence_detector(speech_recognition_payload)

    def _utterance_contains_profanity(
        self, speech_recognition_payload: SimBotSpeechRecognitionPayload
    ) -> bool:
        """Detect whether the turn has profanity in it."""
        try:
            return self._profanity_filter_client.is_profane(speech_recognition_payload.utterance)
        except Exception as err:
            # TODO: What to do if we cannot determine?
            logger.exception("Unable to check for profanity.")
            raise err

    def _utterance_is_out_of_domain(
        self, speech_recognition_payload: SimBotSpeechRecognitionPayload
    ) -> bool:
        """Detect whether the utterance is out of domain or not."""
        try:
            return self._out_of_domain_detector_client.is_out_of_domain(
                speech_recognition_payload.utterance
            )
        except Exception as err:
            # TODO: What to do if we cannot determine?
            logger.exception("Unable to check for out of domain utterance.")
            raise err

    def _utterance_only_contains_wake_word(
        self, speech_recognition_payload: SimBotSpeechRecognitionPayload
    ) -> bool:
        """Detect whether the utterance only contains the wake word or not."""
        return all(token.is_wake_word for token in speech_recognition_payload.tokens)

    def _utterance_is_empty(
        self, speech_recognition_payload: SimBotSpeechRecognitionPayload
    ) -> bool:
        """Detect whether the utterance is empty or not."""
        return not bool(speech_recognition_payload.utterance.strip())
