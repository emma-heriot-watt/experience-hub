import itertools
from collections.abc import Iterator
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import Callable, Optional

from loguru import logger

from emma_experience_hub.api.clients import EmmaPolicyClient
from emma_experience_hub.api.clients.simbot import PlaceholderVisionClient, SimBotFeaturesClient
from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN, PREDICTED_ACTION_DELIMITER
from emma_experience_hub.datamodels import (
    DialogueUtterance,
    EmmaExtractedFeatures,
    EnvironmentStateTurn,
)
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
    SimBotInteractionObject,
    SimBotObjectInteractionPayload,
)
from emma_experience_hub.parsers.simbot import SimBotActionPredictorOutputParser


class SimBotAgentActionGenerationPipeline:
    """Generate an environment interaction for the agent to perform on the environment.

    This class does not handle choosing or generating dialog actions.
    """

    def __init__(
        self,
        features_client: SimBotFeaturesClient,
        button_detector_client: PlaceholderVisionClient,
        action_predictor_client: EmmaPolicyClient,
        action_predictor_response_parser: SimBotActionPredictorOutputParser,
    ) -> None:
        self._features_client = features_client

        self._button_detector_client = button_detector_client

        self._action_predictor_client = action_predictor_client
        self._action_predictor_response_parser = action_predictor_response_parser

    def run(self, session: SimBotSession) -> Optional[SimBotAction]:
        """Generate an action to perform on the environment."""
        if not session.current_turn.intent.agent:
            raise AssertionError("The agent should have an intent before calling this pipeline.")

        try:
            action_intent_handler = self._get_action_intent_handler(
                session.current_turn.intent.agent
            )
        except KeyError:
            logger.debug(
                f"Agent intent ({session.current_turn.intent.agent}) does not require the agent to generate an action that interacts with the environment."
            )
            return None

        try:
            return action_intent_handler(session)
        except Exception:
            logger.error("Failed to convert the agent intent to executable form.")
            return None

    def handle_act_intent(self, session: SimBotSession) -> Optional[SimBotAction]:
        """Generate an action when we want to just act."""
        turns_within_interaction_window = session.get_turns_within_interaction_window()
        environment_state_history = self._get_environment_state_history(
            turns_within_interaction_window,
            self._features_client.get_features,
        )
        dialogue_history = self._get_dialogue_history(turns_within_interaction_window)
        raw_action_prediction = self._action_predictor_client.generate(
            dialogue_history=dialogue_history, environment_state_history=environment_state_history
        )

        # Get the flattened list of extracted features from the state history
        extracted_features = [
            feats for turn in environment_state_history for feats in turn.features
        ]

        # Parse the response into an action
        try:
            return self._action_predictor_response_parser(
                raw_action_prediction,
                extracted_features=extracted_features,
                num_frames_in_current_turn=len(environment_state_history[-1].features),
            )
        except AssertionError:
            logger.error(f"Unable to parse a response for the output {raw_action_prediction}")
            return None

    def handle_press_button_intent(self, session: SimBotSession) -> Optional[SimBotAction]:
        """Generate an action when we want to press a button."""
        if not session.current_turn.speech:
            raise AssertionError("The session turn should have an utterance for this intent.")

        raw_output = f"toggle button {END_OF_TRAJECTORY_TOKEN}{PREDICTED_ACTION_DELIMITER}"
        predicted_mask = self._button_detector_client.get_object_mask_from_image(
            raw_utterance=session.current_turn.speech.utterance,
            # Load the image from the turn's auxiliary metadata file
            # we always use the image in the front view
            image=SimBotAuxiliaryMetadataPayload.from_efs_uri(
                session.current_turn.auxiliary_metadata_uri
            ).images[0],
        )

        # If mask is empty, return None because we failed.
        if not predicted_mask or not predicted_mask[0]:
            logger.error("Predicted mask is empty.")
            return None

        output = SimBotAction(
            id=0,
            type=SimBotActionType.Toggle,
            raw_output=raw_output,
            payload=SimBotObjectInteractionPayload(
                object=SimBotInteractionObject(
                    colorImageIndex=0, mask=predicted_mask, name="button"
                )
            ),
        )

        return output

    def _get_action_intent_handler(
        self, intent: SimBotIntent
    ) -> Callable[[SimBotSession], Optional[SimBotAction]]:
        """Get the handler to use when generating an action to perform on the environment."""
        switcher = {
            SimBotIntentType.act_low_level: self.handle_act_intent,
            SimBotIntentType.press_button: self.handle_press_button_intent,
            # TODO: Add handler for getting the action from the previous turn
            # TODO: Add handler for search
        }

        return switcher[intent.type]

    def _get_dialogue_history(self, turns: list[SimBotSessionTurn]) -> list[DialogueUtterance]:
        """Get a dialogue history from the given turns."""
        utterances_lists = (turn.utterances for turn in turns)
        dialogue_history = list(itertools.chain.from_iterable(utterances_lists))
        return dialogue_history

    def _get_environment_state_history(
        self,
        turns: list[SimBotSessionTurn],
        extracted_features_load_fn: Callable[[SimBotSessionTurn], list[EmmaExtractedFeatures]],
    ) -> list[EnvironmentStateTurn]:
        """Get the environment state history from a set of turns.

        Since we use the threadpool to load features, it does not naturally maintain the order.
        Therefore for each turn submitted, we also track its index to ensure the returned features
        are ordered.
        """
        # Only keep turns which have been used to change the visual frames
        relevant_turns: Iterator[SimBotSessionTurn] = (
            turn
            for turn in turns
            if turn.intent.agent and turn.intent.agent.type == SimBotIntentType.act_low_level
        )

        environment_history: dict[int, EnvironmentStateTurn] = {}

        with ThreadPoolExecutor() as executor:
            # On submitting, the future can be used a key to map to the session turn it came from
            future_to_turn: dict[Future[list[EmmaExtractedFeatures]], SimBotSessionTurn] = {
                executor.submit(extracted_features_load_fn, turn): turn for turn in relevant_turns
            }

            for future in as_completed(future_to_turn):
                turn = future_to_turn[future]
                raw_output = (
                    turn.actions.interaction.raw_output if turn.actions.interaction else None
                )
                try:
                    environment_history[turn.idx] = EnvironmentStateTurn(
                        features=future.result(), output=raw_output
                    )
                except Exception as err:
                    logger.exception("Unable to get features for the turn", exc_info=err)

        # Ensure the environment history is sorted properly and return them
        return list(dict(sorted(environment_history.items())).values())
