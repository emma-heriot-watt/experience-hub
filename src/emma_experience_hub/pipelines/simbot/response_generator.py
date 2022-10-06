from typing import Callable

from emma_experience_hub.api.clients import EmmaPolicyClient, UtteranceGeneratorClient
from emma_experience_hub.api.clients.simbot import SimBotCacheClient
from emma_experience_hub.common.logging import get_logger
from emma_experience_hub.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.simbot import (
    SimBotAction,
    SimBotActionType,
    SimBotIntent,
    SimBotIntentType,
    SimBotSession,
)
from emma_experience_hub.datamodels.simbot.payloads import SimBotDialogPayload
from emma_experience_hub.parsers import NeuralParser


logger = get_logger()

IntentHandlerType = Callable[[SimBotSession], tuple[str, list[SimBotAction]]]


class SimBotResponseGeneratorPipeline:
    """Generate a response for latest session turn."""

    def __init__(
        self,
        extracted_features_cache_client: SimBotCacheClient[list[EmmaExtractedFeatures]],
        utterance_generator_client: UtteranceGeneratorClient,
        instruction_intent_client: EmmaPolicyClient,
        instruction_intent_response_parser: NeuralParser[list[SimBotAction]],
    ) -> None:
        self._extracted_features_cache_client = extracted_features_cache_client

        self._utterance_generator_client = utterance_generator_client

        self._instruction_intent_client = instruction_intent_client
        self._instruction_intent_response_parser = instruction_intent_response_parser

    def run(self, session: SimBotSession) -> SimBotSession:
        """Generate a response for the current session turn."""
        if not session.current_turn.intent:
            raise AssertionError("The session turn should have an intent.")

        # Get the correct handler to use for the given intent
        response_generator_handler = self._get_response_generator_handler(
            session.current_turn.intent
        )

        # Generate the actions for the turn and store within the turn
        raw_output, actions = response_generator_handler(session)

        logger.info(f"Raw output from the response generator: `{raw_output}`")
        logger.info(f"Parsed actions from the response generator: `{actions}`")

        session.current_turn.raw_output = raw_output
        session.current_turn.actions = actions

        return session

    def handle_instruction_intent(self, session: SimBotSession) -> tuple[str, list[SimBotAction]]:
        """Generate a response for the instruction intent."""
        raw_output = self._instruction_intent_client.generate(
            dialogue_history=session.get_dialogue_history(
                session.get_turns_from_most_recent_instruction()
            ),
            environment_state_history=session.get_environment_state_history(
                session.get_turns_from_most_recent_instruction(),
                self._extracted_features_cache_client.load,
            ),
        )

        actions = self._instruction_intent_response_parser(raw_output)

        return raw_output, actions

    def handle_profanity_intent(self, session: SimBotSession) -> tuple[str, list[SimBotAction]]:
        """Generate a response for the profanity intent."""
        return self._handle_intent_with_dialog(
            self._utterance_generator_client.get_profanity_response(), SimBotIntentType.profanity
        )

    def handle_clarify_direction_intent(
        self, session: SimBotSession
    ) -> tuple[str, list[SimBotAction]]:
        """Generate a response for the clarify direction intent."""
        if not session.current_turn.intent:
            raise AssertionError("The session turn should have an intent.")

        return self._handle_intent_with_dialog(
            raw_output=self._utterance_generator_client.get_direction_clarify_question(),
            intent=session.current_turn.intent.type,
        )

    def handle_clarify_description_intent(
        self, session: SimBotSession
    ) -> tuple[str, list[SimBotAction]]:
        """Generate a response for the clarify description intent."""
        if not session.current_turn.intent:
            raise AssertionError("The session turn should have an intent.")

        return self._handle_intent_with_dialog(
            raw_output=self._utterance_generator_client.get_object_description_clarify_question(
                object_name=session.current_turn.intent.object_name
            ),
            intent=session.current_turn.intent.type,
        )

    def handle_clarify_location_intent(
        self, session: SimBotSession
    ) -> tuple[str, list[SimBotAction]]:
        """Generate a response for the clarify location intent."""
        if not session.current_turn.intent:
            raise AssertionError("The session turn should have an intent.")

        return self._handle_intent_with_dialog(
            raw_output=self._utterance_generator_client.get_object_location_clarify_question(
                object_name=session.current_turn.intent.object_name
            ),
            intent=session.current_turn.intent.type,
        )

    def handle_clarify_disambiguation_intent(
        self, session: SimBotSession
    ) -> tuple[str, list[SimBotAction]]:
        """Generate a response for the clarify disambiguation intent."""
        if not session.current_turn.intent:
            raise AssertionError("The session turn should have an intent.")

        return self._handle_intent_with_dialog(
            raw_output=self._utterance_generator_client.get_object_disambiguation_clarify_question(
                object_name=session.current_turn.intent.object_name
            ),
            intent=session.current_turn.intent.type,
        )

    def _get_response_generator_handler(self, intent: SimBotIntent) -> IntentHandlerType:
        """Get the correct handler to generate a response for the given intent."""
        switcher: dict[SimBotIntentType, IntentHandlerType] = {
            SimBotIntentType.instruction: self.handle_instruction_intent,
            SimBotIntentType.profanity: self.handle_profanity_intent,
            SimBotIntentType.clarify_direction: self.handle_clarify_direction_intent,
            SimBotIntentType.clarify_description: self.handle_clarify_description_intent,
            SimBotIntentType.clarify_location: self.handle_clarify_location_intent,
            SimBotIntentType.clarify_disambiguation: self.handle_clarify_disambiguation_intent,
        }
        return switcher[intent.type]

    def _handle_intent_with_dialog(
        self, raw_output: str, intent: SimBotIntentType
    ) -> tuple[str, list[SimBotAction]]:
        """Create the return payload for dialog responses.

        Basically, just reduce the boilerplate.
        """
        action = [
            SimBotAction(
                type=SimBotActionType.Dialog,
                payload=SimBotDialogPayload(value=raw_output, intent=intent),
            )
        ]

        return raw_output, action
