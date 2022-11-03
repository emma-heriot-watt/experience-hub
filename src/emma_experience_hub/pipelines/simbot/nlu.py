from typing import Optional

from loguru import logger

from emma_experience_hub.api.clients import (
    EmmaPolicyClient,
    OutOfDomainDetectorClient,
    ProfanityFilterClient,
)
from emma_experience_hub.api.clients.simbot import SimBotCacheClient
from emma_experience_hub.constants.simbot import get_simbot_is_press_button_verbs
from emma_experience_hub.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.simbot import (
    SimBotIntent,
    SimBotIntentType,
    SimBotSession,
    SimBotSessionTurn,
)
from emma_experience_hub.datamodels.simbot.payloads import SimBotSpeechRecognitionPayload
from emma_experience_hub.parsers import NeuralParser, Parser


class SimBotNLUPipeline:
    """Process the latest session turn and return the intent."""

    _disable_clarification_intents: bool = True

    def __init__(
        self,
        extracted_features_cache_client: SimBotCacheClient[list[EmmaExtractedFeatures]],
        profanity_filter_client: ProfanityFilterClient,
        out_of_domain_detector_client: OutOfDomainDetectorClient,
        nlu_intent_client: EmmaPolicyClient,
        nlu_intent_parser: NeuralParser[SimBotIntent],
        asr_confidence_filter: Parser[SimBotSpeechRecognitionPayload, bool],
    ) -> None:
        self._extracted_features_cache_client = extracted_features_cache_client
        self._profanity_filter_client = profanity_filter_client
        self._out_of_domain_detector_client = out_of_domain_detector_client
        self._asr_confidence_filter = asr_confidence_filter

        self._nlu_intent_client = nlu_intent_client
        self._nlu_intent_parser = nlu_intent_parser
        self._is_press_button_verbs = get_simbot_is_press_button_verbs()

    def run(self, session: SimBotSession) -> SimBotSession:  # noqa: WPS212
        """Run the pipeline for the session."""
        # If we have arena errors from the actions we performed, give feedback for them
        action_status_intent = self._try_convert_action_status_to_intent(session)
        if action_status_intent:
            logger.debug("Received error status from arena and will provide feedback for it.")
            session.current_turn.intent = SimBotIntent(type=action_status_intent)
            return session

        if self._should_respond_with_end_of_trajectory_intent(session):
            session.current_turn.intent = SimBotIntent(type=SimBotIntentType.end_of_trajectory)
            return session

        # Bypass the NLU pipeline if there is no utterance to extract intent from
        if not session.current_turn.speech:
            logger.debug(
                "There is no utterance to extract intent from. Assume we just need to act."
            )
            session.current_turn.intent = SimBotIntent(type=SimBotIntentType.instruction)
            return session

        # Check whether or not the utterance contains profanity
        if self._utterance_contains_profanity(session.current_turn):
            logger.debug("Utterance contains profanity.")
            session.current_turn.intent = SimBotIntent(type=SimBotIntentType.profanity)
            return session

        # Check whether our confidence is above a certain threshold
        if not self._asr_confidence_filter(session.current_turn.speech):
            logger.debug("ASR confidence is too low; therefore we cannot understand the user.")
            session.current_turn.intent = SimBotIntent(type=SimBotIntentType.low_asr_confidence)
            return session

        # Check whether or not the utterance is out of domain
        if self._utterance_is_out_of_domain(session.current_turn):
            logger.debug("Utterance is out of domain.")
            session.current_turn.intent = SimBotIntent(type=SimBotIntentType.out_of_domain)
            return session

        if self._utterance_is_press_button(session.current_turn):
            logger.debug("Utterance is to press the button.")
            session.current_turn.intent = SimBotIntent(type=SimBotIntentType.press_button)
            return session

        # Extract the intent, store within the session, and return
        session.current_turn.intent = self.extract_intent(session)
        return session

    def extract_intent(self, session: SimBotSession) -> SimBotIntent:
        """Extract the intent from the given turn."""
        raw_intent = self._nlu_intent_client.generate(
            dialogue_history=session.current_turn.utterances,
            environment_state_history=session.get_environment_state_history(
                [session.current_turn],
                self._extracted_features_cache_client.load,
            ),
        )
        intent = self._nlu_intent_parser(raw_intent)
        logger.info(f"Extracted intent from turn: {intent}")

        if self._disable_clarification_intents:
            logger.info("Clarification questions are disabled, returning the `<act>` intent.")
            return SimBotIntent(type=SimBotIntentType.instruction)

        return intent

    def _utterance_contains_profanity(self, turn: SimBotSessionTurn) -> bool:
        """Detect whether the turn has profanity in it."""
        # Return False if there is no utterance
        if turn.speech is None:
            return False

        try:
            return self._profanity_filter_client.is_profane(turn.speech.utterance)
        except Exception as err:
            # TODO: What to do if we cannot determine?
            logger.exception("Unable to check for profanity.", exc_info=err)
            raise err

    def _utterance_is_out_of_domain(self, turn: SimBotSessionTurn) -> bool:
        """Detect whether the utterance is out of domain or not."""
        # Return False if there is no utterance
        if turn.speech is None:
            return False

        try:
            return self._out_of_domain_detector_client.is_out_of_domain(turn.speech.utterance)
        except Exception as err:
            # TODO: What to do if we cannot determine?
            logger.exception("Unable to check for out of domain utterance.", exc_info=err)
            raise err

    def _should_respond_with_end_of_trajectory_intent(self, session: SimBotSession) -> bool:
        """Detect whether the previous turn contains the end of trajectory."""
        # If speech is recieved, always handle the speech
        if session.current_turn.speech:
            return False

        # For there to be a previous turn, there must be at least 2 of them.
        if session.num_turns < 2:
            return False

        # Check if the raw output contains the end of trajectory token
        return session.turns[-2].output_contains_end_of_trajectory_token

    def _utterance_is_press_button(self, turn: SimBotSessionTurn) -> bool:
        """Detect whether the utterance is for pressing the buttom.

        Adopted from https://github.com/emma-simbot/simbot-ml-toolbox/blob/8a697b32b47794f37b4dc481753f7e66de358efb/action_model/placeholder_model.py#L165-L579
        """
        is_press_button = False
        if turn.speech is not None:
            utterance = turn.speech.utterance.lower()
            if "button" in utterance:
                is_press_button = any([verb in utterance for verb in self._is_press_button_verbs])
        return is_press_button

    def _try_convert_action_status_to_intent(
        self, session: SimBotSession
    ) -> Optional[SimBotIntentType]:
        """Return True if we should provide feedback from the returned actions from the arena."""
        # If there is no previous turn
        if not session.previous_turn:
            return None

        # If all previous actions were successful
        if session.previous_turn.all_actions_are_successful:
            return None

        # If we do not have the last action status from the previous turn
        if not session.previous_turn.last_action_status_type:
            return None

        # If we are unable to convert the action status to one of the intents we handle
        try:
            return SimBotIntentType[session.previous_turn.last_action_status_type.name]
        except (ValueError, KeyError):
            return None
