from typing import Callable

from loguru import logger

from emma_experience_hub.api.clients import EmmaPolicyClient, UtteranceGeneratorClient
from emma_experience_hub.api.clients.simbot import PlaceholderVisionClient, SimBotCacheClient
from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN
from emma_experience_hub.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.simbot import (
    SimBotAction,
    SimBotActionType,
    SimBotIntent,
    SimBotIntentType,
    SimBotSession,
    SimBotSessionTurn,
)
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotAuxiliaryMetadataPayload,
    SimBotDialogPayload,
    SimBotInteractionObject,
    SimBotObjectInteractionPayload,
)
from emma_experience_hub.parsers.simbot import SimBotActionPredictorOutputParser


ResponseGeneratorHandlerReturnType = tuple[str, list[SimBotAction]]


class SimBotResponseGeneratorPipeline:
    """Generate a response for latest session turn."""

    def __init__(
        self,
        extracted_features_cache_client: SimBotCacheClient[list[EmmaExtractedFeatures]],
        utterance_generator_client: UtteranceGeneratorClient,
        button_detector_client: PlaceholderVisionClient,
        instruction_intent_client: EmmaPolicyClient,
        instruction_intent_response_parser: SimBotActionPredictorOutputParser,
    ) -> None:
        self._extracted_features_cache_client = extracted_features_cache_client

        self._utterance_generator_client = utterance_generator_client
        self._button_detector_client = button_detector_client

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
        logger.info(f"Parsed action from the response generator: `{actions}`")

        session.current_turn.raw_output = raw_output
        session.current_turn.actions = actions

        if END_OF_TRAJECTORY_TOKEN in raw_output:
            _, end_of_trajectory_dialog_action = self.handle_end_of_trajectory_intent(session)
            actions.extend(end_of_trajectory_dialog_action)

        # Ensure that all the actions are indexed correctly before returning
        self._update_action_ids_for_turn(session.current_turn)

        return session

    def handle_instruction_intent(
        self, session: SimBotSession
    ) -> ResponseGeneratorHandlerReturnType:
        """Generate a response for the instruction intent."""
        environment_state_history = session.get_environment_state_history(
            session.get_turns_since_local_state_reset(),
            self._extracted_features_cache_client.load,
        )
        raw_output = self._instruction_intent_client.generate(
            dialogue_history=session.get_dialogue_history(
                session.get_turns_since_local_state_reset()
            ),
            environment_state_history=environment_state_history,
        )
        # get the flattened list of extracted features from the state history
        extracted_features = [
            feats for turn in environment_state_history for feats in turn.features
        ]
        try:
            actions = [
                self._instruction_intent_response_parser(
                    raw_output,
                    extracted_features=extracted_features,
                    num_frames_in_current_turn=len(environment_state_history[-1].features),
                )
            ]
        except AssertionError:
            actions = [
                SimBotAction(
                    id=0,
                    type=SimBotActionType.Dialog,
                    payload=SimBotDialogPayload(
                        value=self._utterance_generator_client.get_raised_exception_response()
                    ),
                )
            ]

        return raw_output, actions

    def handle_profanity_intent(
        self, session: SimBotSession
    ) -> ResponseGeneratorHandlerReturnType:
        """Generate a response for the profanity intent."""
        return self._handle_intent_with_dialog(
            self._utterance_generator_client.get_profanity_response(), SimBotIntentType.profanity
        )

    def handle_clarify_direction_intent(
        self, session: SimBotSession
    ) -> ResponseGeneratorHandlerReturnType:
        """Generate a response for the clarify direction intent."""
        if not session.current_turn.intent:
            raise AssertionError("The session turn should have an intent.")

        return self._handle_intent_with_dialog(
            raw_output=self._utterance_generator_client.get_direction_clarify_question(),
            intent=session.current_turn.intent.type,
        )

    def handle_clarify_description_intent(
        self, session: SimBotSession
    ) -> ResponseGeneratorHandlerReturnType:
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
    ) -> ResponseGeneratorHandlerReturnType:
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
    ) -> ResponseGeneratorHandlerReturnType:
        """Generate a response for the clarify disambiguation intent."""
        if not session.current_turn.intent:
            raise AssertionError("The session turn should have an intent.")

        return self._handle_intent_with_dialog(
            raw_output=self._utterance_generator_client.get_object_disambiguation_clarify_question(
                object_name=session.current_turn.intent.object_name
            ),
            intent=session.current_turn.intent.type,
        )

    def handle_end_of_trajectory_intent(
        self, session: SimBotSession
    ) -> ResponseGeneratorHandlerReturnType:
        """Generate a response when the previous turn was the end of the action trajectory."""
        if not session.current_turn.intent:
            raise AssertionError("The session turn should have an intent.")

        # Default to the "done" response
        raw_output = self._utterance_generator_client.get_finished_response()

        return self._handle_intent_with_dialog(raw_output, SimBotIntentType.end_of_trajectory)

    def handle_out_of_domain_intent(
        self, session: SimBotSession
    ) -> ResponseGeneratorHandlerReturnType:
        """Generate a response when the utterance is out of the domain."""
        if not session.current_turn.intent:
            raise AssertionError("The session turn should have an intent.")

        return self._handle_intent_with_dialog(
            raw_output=self._utterance_generator_client.get_out_of_domain_response(),
            intent=session.current_turn.intent.type,
        )

    def handle_low_asr_confidence_intent(
        self, session: SimBotSession
    ) -> ResponseGeneratorHandlerReturnType:
        """Generate a response when the average confidence of the ASR output is too low."""
        if not session.current_turn.intent:
            raise AssertionError("The session turn should have an intent.")

        return self._handle_intent_with_dialog(
            raw_output=self._utterance_generator_client.get_too_low_asr_confidence_response(),
            intent=session.current_turn.intent.type,
        )

    def handle_press_button_intent(
        self, session: SimBotSession
    ) -> ResponseGeneratorHandlerReturnType:
        """Generate a response when we want to press a button."""
        if not session.current_turn.intent:
            raise AssertionError("The session turn should have an intent.")

        if not session.current_turn.speech:
            raise AssertionError("The session turn should have an utterance for this intent.")

        raw_output = "press button <stop>.</s>"
        predicted_mask = self._button_detector_client.get_object_mask_from_image(
            raw_utterance=session.current_turn.speech.utterance,
            # Load the image from the turn's auxiliary metadata file
            # we always use the image in the front view
            image=SimBotAuxiliaryMetadataPayload.from_efs_uri(
                session.current_turn.auxiliary_metadata_uri
            ).images[0],
        )
        non_empty_mask = predicted_mask and predicted_mask[0]

        if not non_empty_mask:
            actions = [
                SimBotAction(
                    id=0,
                    type=SimBotActionType.Dialog,
                    payload=SimBotDialogPayload(
                        value=self._utterance_generator_client.get_raised_exception_for_lack_of_buttons()
                    ),
                )
            ]

            return raw_output, actions

        output = SimBotAction(
            id=0,
            type=SimBotActionType.Toggle,
            payload=SimBotObjectInteractionPayload(
                object=SimBotInteractionObject(
                    colorImageIndex=0,
                    mask=predicted_mask,
                    name="button",
                )
            ),
        )

        return raw_output, [output]

    def _get_response_generator_handler(
        self, intent: SimBotIntent
    ) -> Callable[[SimBotSession], ResponseGeneratorHandlerReturnType]:
        """Get the correct handler to generate a response for the given intent."""
        switcher: dict[
            SimBotIntentType, Callable[[SimBotSession], ResponseGeneratorHandlerReturnType]
        ] = {
            SimBotIntentType.instruction: self.handle_instruction_intent,
            SimBotIntentType.profanity: self.handle_profanity_intent,
            SimBotIntentType.clarify_direction: self.handle_clarify_direction_intent,
            SimBotIntentType.clarify_description: self.handle_clarify_description_intent,
            SimBotIntentType.clarify_location: self.handle_clarify_location_intent,
            SimBotIntentType.clarify_disambiguation: self.handle_clarify_disambiguation_intent,
            SimBotIntentType.end_of_trajectory: self.handle_end_of_trajectory_intent,
            SimBotIntentType.out_of_domain: self.handle_out_of_domain_intent,
            SimBotIntentType.low_asr_confidence: self.handle_low_asr_confidence_intent,
            SimBotIntentType.press_button: self.handle_press_button_intent,
        }
        return switcher[intent.type]

    def _handle_intent_with_dialog(
        self, raw_output: str, intent: SimBotIntentType
    ) -> ResponseGeneratorHandlerReturnType:
        """Create the return payload for dialog responses.

        Basically, just reduce the boilerplate.
        """
        action = [
            SimBotAction(
                id=0,
                type=SimBotActionType.Dialog,
                payload=SimBotDialogPayload(value=raw_output, intent=intent),
            )
        ]

        return raw_output, action

    def _update_action_ids_for_turn(self, turn: SimBotSessionTurn) -> None:
        """Reset the action IDs for the turn."""
        if not turn.actions:
            raise AssertionError(
                "The turn must have actions before calling this method. This method should only be called at the end of the pipeline."
            )

        for action_idx, action in enumerate(turn.actions):
            action.id = action_idx
