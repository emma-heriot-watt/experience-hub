from typing import Optional

from loguru import logger
from opentelemetry import trace

from emma_common.datamodels import EmmaExtractedFeatures, EnvironmentStateTurn
from emma_experience_hub.api.clients.simbot import (
    SimbotActionPredictionClient,
    SimBotFeaturesClient,
)
from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN, PREDICTED_ACTION_DELIMITER
from emma_experience_hub.datamodels.common import GFHLocationType
from emma_experience_hub.datamodels.enums import SearchPlannerType
from emma_experience_hub.datamodels.simbot import SimBotAction, SimBotActionType, SimBotSession
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotInteractionObject,
    SimBotObjectInteractionPayload,
    SimBotObjectMaskType,
)
from emma_experience_hub.functions.simbot import (
    BasicSearchPlanner,
    GrabFromHistory,
    GreedyMaximumVertexCoverSearchPlanner,
    SearchPlanner,
    SimBotSceneObjectTokens,
    class_label_is_unique_in_frame,
    get_class_name_from_special_tokens,
    get_correct_frame_index,
    get_mask_from_special_tokens,
)
from emma_experience_hub.parsers.simbot import SimBotVisualGroundingOutputParser


tracer = trace.get_tracer(__name__)


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
        search_planner: SearchPlanner,
        enable_grab_from_history: bool = True,
        _enable_scanning_found_object: bool = True,
        scan_area_threshold: float = 200,
    ) -> None:
        self._features_client = features_client

        self._action_predictor_client = action_predictor_client
        self._visual_grounding_output_parser = visual_grounding_output_parser

        self._search_planner = search_planner
        self._enable_grab_from_history = enable_grab_from_history
        self._grab_from_history = GrabFromHistory()
        self._enable_scanning_found_object = _enable_scanning_found_object
        self._scan_area_threshold = scan_area_threshold

    @classmethod
    def from_planner_type(
        cls,
        features_client: SimBotFeaturesClient,
        action_predictor_client: SimbotActionPredictionClient,
        visual_grounding_output_parser: SimBotVisualGroundingOutputParser,
        planner_type: SearchPlannerType = SearchPlannerType.greedy_max_vertex_cover,
        distance_threshold: float = 4,
        viewpoint_budget: int = 2,
        enable_grab_from_history: bool = True,
        gfh_location_type: GFHLocationType = GFHLocationType.location,
        _enable_scanning_found_object: bool = True,
        scan_area_threshold: float = 200,
    ) -> "SimBotFindObjectPipeline":
        """Instantiate the pipeline from the SearchPlannerType."""
        planners = {
            SearchPlannerType.basic: BasicSearchPlanner(),
            SearchPlannerType.greedy_max_vertex_cover: GreedyMaximumVertexCoverSearchPlanner(
                distance_threshold=distance_threshold,
                vertex_budget=viewpoint_budget,
                gfh_location_type=gfh_location_type,
            ),
        }

        return cls(
            features_client=features_client,
            action_predictor_client=action_predictor_client,
            visual_grounding_output_parser=visual_grounding_output_parser,
            search_planner=planners[planner_type],
            enable_grab_from_history=enable_grab_from_history,
            _enable_scanning_found_object=_enable_scanning_found_object,
            scan_area_threshold=scan_area_threshold,
        )

    def run(self, session: SimBotSession) -> Optional[SimBotAction]:
        """Handle the search through the environment."""
        if self._should_start_new_search(session):
            logger.debug("Preparing search plan...")
            with tracer.start_as_current_span("Building search plan"):
                search_plan = self._build_search_plan(session)

            if self._should_goto_room_before_new_search(search_plan):
                return search_plan[0]
            # Reset the queue and counter and add the search plan
            session.current_state.find_queue.reset()
            session.current_state.find_queue.extend_tail(search_plan)

        if self._should_reset_utterance_queue(session):
            logger.debug("Find queue is empty; returning None")
            self._search_planner.reset_utterance_queue_if_object_not_found(session)
            return None

        if self._should_goto_found_object(session):
            return self._goto_scanned_object(session)

        extracted_features = self._features_client.get_features(session.current_turn)
        session.update_agent_memory(extracted_features)

        # Try to find the object in the previous turn
        try:
            decoded_scene_object_tokens = self._get_object_from_turn(session, extracted_features)
        except AssertionError:
            # If the object has not been found, get the next action to perform
            return self._get_next_action_from_plan(session)

        # If the object has been found create the sequence of actions
        return self._create_actions_for_found_object(
            session, decoded_scene_object_tokens, extracted_features
        )

    def _can_search_from_history(self, session: SimBotSession) -> bool:
        """Determine if we should search in history."""
        if not self._enable_grab_from_history:
            return False
        # Check that there is an entity to search history for
        if session.current_turn.intent.physical_interaction is None:
            return False

        return session.current_turn.intent.physical_interaction.entity is not None

    def _build_search_plan(self, session: SimBotSession) -> list[SimBotAction]:
        """Build a plan of actions for the current session."""
        if self._can_search_from_history(session):
            return self._grab_from_history(session, search_planner=self._search_planner)

        return self._search_planner.run(session)

    def _should_start_new_search(self, session: SimBotSession) -> bool:
        """Should we be starting a new search?

        If the queue is empty, start a new one. If the queue is not empty, do not.
        """
        return not session.is_find_object_in_progress

    def _should_goto_room_before_new_search(self, search_plan: list[SimBotAction]) -> bool:
        """Should we go to another room before starting the search?"""
        if not search_plan:
            return False
        return search_plan[0].type == SimBotActionType.GotoRoom

    def _should_reset_utterance_queue(self, session: SimBotSession) -> bool:
        """Should we reset the utterance queue?

        The queue is empty but the previous action ia not a look around.
        """
        is_previous_action_look_around = (
            session.previous_valid_turn is not None
            and session.previous_valid_turn.is_look_around_from_search
        )
        return session.current_state.find_queue.is_empty and not is_previous_action_look_around

    def _should_goto_found_object(self, session: SimBotSession) -> bool:
        """Should we go to the highlighted object?

        The queue contain has a goto action at its head whenever we have found an object.
        """
        if not self._enable_scanning_found_object:
            return False
        head_action = session.current_state.find_queue.queue[0]
        return head_action.type == SimBotActionType.GotoObject

    def _should_scan_found_object(
        self,
        session: SimBotSession,
        scene_object_tokens: SimBotSceneObjectTokens,
        found_object_label: str,
        extracted_features: list[EmmaExtractedFeatures],
    ) -> bool:
        """Should we highlight the found object?"""
        if not self._enable_scanning_found_object:
            return False
        # Do not highlight objects when the intent is a search and no_match / missing_inventory
        # Go straight to the object and execute the original instruction
        if session.current_turn.intent.is_searching_inferred_object:
            return False

        frame_idx = scene_object_tokens.frame_index

        class_is_unique = class_label_is_unique_in_frame(
            frame_index=frame_idx,
            class_label=found_object_label,
            extracted_features=extracted_features,
        )

        object_idx = scene_object_tokens.object_index - 1
        area = extracted_features[frame_idx - 1].bbox_areas[object_idx].item()
        return class_is_unique and area > self._scan_area_threshold

    def _next_action_is_dummy(self, session: SimBotSession) -> bool:
        """Is the next action in the queue a dummy move forward?"""
        head_action = session.current_state.find_queue.queue[0]
        return head_action.type == SimBotActionType.MoveForward

    @tracer.start_as_current_span("Trying to find object from visuals")
    def _get_object_from_turn(
        self,
        session: SimBotSession,
        extracted_features: list[EmmaExtractedFeatures],
    ) -> SimBotSceneObjectTokens:
        """Try to get the visual token and frame token from the previous turns."""
        # Only use the incoming turn for visual features but get the utterances from the
        # interation window (i.e. since the search action started)
        dialogue_history = session.get_dialogue_history_from_session_turns(
            session.get_turns_since_last_user_utterance(), include_agent_responses=False
        )

        raw_visual_grounding_output = self._action_predictor_client.find_object_in_scene(
            dialogue_history=dialogue_history,
            environment_state_history=[EnvironmentStateTurn(features=extracted_features)],
        )

        with tracer.start_as_current_span("Parse visual grounding output"):
            scene_object_tokens = self._visual_grounding_output_parser(raw_visual_grounding_output)

        if scene_object_tokens is None:
            raise AssertionError("Unable to get scene object tokens from the model output.")

        return scene_object_tokens

    @tracer.start_as_current_span("Create actions for the found object")
    def _create_actions_for_found_object(
        self,
        session: SimBotSession,
        scene_object_tokens: SimBotSceneObjectTokens,
        extracted_features: list[EmmaExtractedFeatures],
    ) -> SimBotAction:
        """Create the actions when the object has been found."""
        if scene_object_tokens.object_index is None:
            raise AssertionError("The object index for the object should not be None.")

        object_mask = get_mask_from_special_tokens(
            scene_object_tokens.frame_index,
            scene_object_tokens.object_index,
            extracted_features,
        )

        object_name = get_class_name_from_special_tokens(
            scene_object_tokens.frame_index,
            scene_object_tokens.object_index,
            extracted_features,
        )

        if object_name.lower() == "embiggenator":
            try:
                object_mask = self._features_client.get_mask_for_embiggenator(session.current_turn)
            except Exception:
                logger.warning("Unable to replace mask for the embiggenator")

        color_image_index = get_correct_frame_index(
            parsed_frame_index=scene_object_tokens.frame_index,
            num_frames_in_current_turn=len(extracted_features),
            num_total_frames=len(extracted_features),
        )

        should_scan_found_object = self._should_scan_found_object(
            session,
            scene_object_tokens=scene_object_tokens,
            found_object_label=object_name,
            extracted_features=extracted_features,
        )
        goto_action = self._create_action_from_scene_object(
            action_type=SimBotActionType.GotoObject,
            object_mask=object_mask,
            frame_index=scene_object_tokens.frame_index,
            object_index=scene_object_tokens.object_index,
            color_image_index=color_image_index,
            name=object_name,
            add_stop_token=True,
        )

        session.current_state.find_queue.reset()
        if should_scan_found_object:
            scan_action = self._create_action_from_scene_object(
                action_type=SimBotActionType.Scan,
                object_mask=object_mask,
                frame_index=scene_object_tokens.frame_index,
                object_index=scene_object_tokens.object_index,
                color_image_index=color_image_index,
                name=object_name,
            )
            session.current_state.find_queue.append_to_head(goto_action)
            return scan_action
        # Go straight to the object and execute the original instruction
        return goto_action

    def _goto_scanned_object(self, session: SimBotSession) -> Optional[SimBotAction]:
        """Create the actions when the object has been found."""
        logger.warning("Clearing the find queue of the session")
        session.current_state.find_queue.reset()
        extracted_features = self._features_client.get_features(session.current_turn)
        session.update_agent_memory(extracted_features)
        # Try to find the object in the current turn
        try:
            scene_object_tokens = self._get_object_from_turn(session, extracted_features)
        except AssertionError:
            # Skip the scan if the policy model fails to find the object
            return None

        if scene_object_tokens.object_index is None:
            raise AssertionError("The object index for the object should not be None.")

        object_mask = get_mask_from_special_tokens(
            scene_object_tokens.frame_index,
            scene_object_tokens.object_index,
            extracted_features,
        )

        object_name = get_class_name_from_special_tokens(
            scene_object_tokens.frame_index,
            scene_object_tokens.object_index,
            extracted_features,
        )

        if object_name.lower() == "embiggenator":
            try:
                object_mask = self._features_client.get_mask_for_embiggenator(session.current_turn)
            except Exception:
                logger.warning("Unable to replace mask for the embiggenator")

        color_image_index = get_correct_frame_index(
            parsed_frame_index=scene_object_tokens.frame_index,
            num_frames_in_current_turn=len(extracted_features),
            num_total_frames=len(extracted_features),
        )

        goto_action = self._create_action_from_scene_object(
            action_type=SimBotActionType.GotoObject,
            object_mask=object_mask,
            frame_index=scene_object_tokens.frame_index,
            object_index=scene_object_tokens.object_index,
            color_image_index=color_image_index,
            add_stop_token=True,
            name=object_name,
        )
        return goto_action

    def _create_action_from_scene_object(
        self,
        action_type: SimBotActionType,
        object_mask: SimBotObjectMaskType,
        frame_index: int,
        object_index: int,
        color_image_index: int,
        name: str = "",
        add_stop_token: bool = False,
    ) -> SimBotAction:
        """Create an action from a found scene object."""
        if add_stop_token:
            output_suffix = f"{END_OF_TRAJECTORY_TOKEN}{PREDICTED_ACTION_DELIMITER}"
        else:
            output_suffix = PREDICTED_ACTION_DELIMITER
        raw_output = f"{action_type.value} <frame_token_{frame_index}> <vis_token_{object_index}> {output_suffix}"
        return SimBotAction(
            id=0,
            type=action_type,
            raw_output=raw_output,
            payload=SimBotObjectInteractionPayload(
                object=SimBotInteractionObject(
                    colorImageIndex=color_image_index,
                    mask=object_mask,
                    name=name,
                )
            ),
        )

    @tracer.start_as_current_span("Try get next action from plan")
    def _get_next_action_from_plan(self, session: SimBotSession) -> Optional[SimBotAction]:
        """If the model did not find the object, get the next action from the search plan."""
        next_action: Optional[SimBotAction] = None
        try:
            logger.debug("get the next action from the search plan")
            next_action = session.current_state.find_queue.pop_from_head()
        except IndexError:
            logger.debug("No more actions remaining within the search plan")
        # Reset the utterance queue if there is no next action or the next action is end-of-trajectory
        self._search_planner.reset_utterance_queue_if_object_not_found(session, next_action)
        return next_action
