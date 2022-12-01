from typing import Optional

from loguru import logger

from emma_experience_hub.api.clients.simbot import (
    SimbotActionPredictionClient,
    SimBotFeaturesClient,
)
from emma_experience_hub.datamodels import EmmaExtractedFeatures, EnvironmentStateTurn
from emma_experience_hub.datamodels.simbot import SimBotAction, SimBotActionType, SimBotSession
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotInteractionObject,
    SimBotLookAroundPayload,
    SimBotObjectInteractionPayload,
    SimBotObjectMaskType,
)
from emma_experience_hub.functions.simbot import (
    SimBotSceneObjectTokens,
    get_correct_frame_index,
    get_mask_from_special_tokens,
)
from emma_experience_hub.parsers.simbot import SimBotVisualGroundingOutputParser


class SimBotFindObjectPipeline:
    """Pipeline to allow the agent to find object within the arena.

    This pipeline follows the skeleton outlined by the `SimBotAgentActionGenerationPipeline` since
    it does similar things.
    """

    def __init__(
        self,
        features_client: SimBotFeaturesClient,
        action_predictor_client: SimbotActionPredictionClient,
        visual_grounding_output_parser: SimBotVisualGroundingOutputParser,
    ) -> None:
        self._features_client = features_client

        self._action_predictor_client = action_predictor_client
        self._visual_grounding_output_parser = visual_grounding_output_parser

    def run(self, session: SimBotSession) -> Optional[SimBotAction]:
        """Handle the search through the environment."""
        if self._should_start_new_search(session):
            logger.debug("Preparing search plan...")
            search_plan = self.prepare_search_plan(session)

            # Reset the queue and counter and add the search plan
            session.current_state.find_queue.reset()
            session.current_state.find_queue.extend_tail(search_plan)

        extracted_features = self._features_client.get_features(session.current_turn)

        # Try to find the object in the previous turn
        try:
            decoded_scene_object_tokens = self._get_object_from_previous_turn(
                session, extracted_features
            )
        except AssertionError:
            # If the object has not been found, get the next action to perform
            return self._get_next_action_from_plan(session)

        # If the object has been found, create the highlight action and clear the plan
        session.current_state.find_queue.reset()
        return self._create_highlight_action_from_scene_object(
            decoded_scene_object_tokens, extracted_features
        )

    def prepare_search_plan(self, session: SimBotSession) -> list[SimBotAction]:
        """Plan out the actions the agent will take to perform the search."""
        look_around_action = SimBotAction(
            id=0,
            type=SimBotActionType.Look,
            raw_output="look around.",
            payload=SimBotLookAroundPayload(),
        )

        search_plan = [look_around_action]

        logger.debug(f"Built search plan: {search_plan}")
        return search_plan

    def _should_start_new_search(self, session: SimBotSession) -> bool:
        """Should we be starting a new search?

        If the queue is empty, start a enw one. If the queue is not empty,do not.
        """
        return session.current_state.find_queue.is_empty

    def _get_object_from_previous_turn(
        self,
        session: SimBotSession,
        extracted_features: list[EmmaExtractedFeatures],
    ) -> SimBotSceneObjectTokens:
        """Try to get the visual token and frame token from the previous turns."""
        # Only use the incoming turn for visual features but get the utterances from the
        # interation window (i.e. since the search action started)
        dialogue_history = session.get_dialogue_history_from_session_turns(
            session.get_turns_within_interaction_window()
        )
        raw_visual_grounding_output = self._action_predictor_client.find_object_in_scene(
            dialogue_history=dialogue_history,
            environment_state_history=[EnvironmentStateTurn(features=extracted_features)],
        )

        scene_object_tokens = self._visual_grounding_output_parser(raw_visual_grounding_output)

        if scene_object_tokens is None:
            raise AssertionError("Unable to get scene object tokens from the model output.")

        return scene_object_tokens

    def _create_highlight_action_from_scene_object(
        self,
        scene_object_tokens: SimBotSceneObjectTokens,
        extracted_features: list[EmmaExtractedFeatures],
    ) -> SimBotAction:
        """Convert the decoded scene object into a highlight action for the user."""
        if scene_object_tokens.object_index is None:
            raise AssertionError("The object index for the object should not be None.")

        object_mask = get_mask_from_special_tokens(
            scene_object_tokens.frame_index, scene_object_tokens.object_index, extracted_features
        )
        correct_frame_index = get_correct_frame_index(
            parsed_frame_index=scene_object_tokens.frame_index,
            num_frames_in_current_turn=len(extracted_features),
            num_total_frames=len(extracted_features),
        )

        return self._create_action_from_scene_object(
            SimBotActionType.Highlight, scene_object_tokens, correct_frame_index, object_mask
        )

    def _create_action_from_scene_object(
        self,
        action_type: SimBotActionType,
        scene_object_tokens: SimBotSceneObjectTokens,
        color_image_index: int,
        object_mask: SimBotObjectMaskType,
        object_name: str = "",
    ) -> SimBotAction:
        """Create a SimBotAction from the scene object."""
        return SimBotAction(
            id=0,
            type=action_type,
            raw_output=f"{action_type.value} <frame_token_{scene_object_tokens.frame_index}> <vis_token_{scene_object_tokens.object_index}.",
            payload=SimBotObjectInteractionPayload(
                object=SimBotInteractionObject(
                    colorImageIndex=color_image_index,
                    mask=object_mask,
                    # TODO: do we need an object name? What if we need the closest stickynote?
                    name=object_name,
                )
            ),
        )

    def _get_next_action_from_plan(self, session: SimBotSession) -> Optional[SimBotAction]:
        """If the model did not find the object, get the next action from the search plan."""
        try:
            return session.current_state.find_queue.pop_from_head()
        except IndexError:
            logger.debug("No more actions remaining within the search plan")
            return None
