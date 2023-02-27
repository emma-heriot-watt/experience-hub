from typing import Optional

from loguru import logger
from opentelemetry import trace

from emma_common.datamodels import EmmaExtractedFeatures, EnvironmentStateTurn
from emma_experience_hub.api.clients.simbot import (
    SimbotActionPredictionClient,
    SimBotFeaturesClient,
)
from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN, PREDICTED_ACTION_DELIMITER
from emma_experience_hub.datamodels.enums import SearchPlannerType
from emma_experience_hub.datamodels.simbot import SimBotAction, SimBotActionType, SimBotSession
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotInteractionObject,
    SimBotObjectInteractionPayload,
    SimBotObjectMaskType,
)
from emma_experience_hub.functions.simbot import (
    BasicSearchPlanner,
    GreedyMaximumVertexCoverSearchPlanner,
    SearchPlanner,
    SimBotSceneObjectTokens,
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
    ) -> None:
        self._features_client = features_client

        self._action_predictor_client = action_predictor_client
        self._visual_grounding_output_parser = visual_grounding_output_parser

        self._search_planner = search_planner
        self._enable_grab_from_history = enable_grab_from_history

    @classmethod
    def from_planner_type(
        cls,
        features_client: SimBotFeaturesClient,
        action_predictor_client: SimbotActionPredictionClient,
        visual_grounding_output_parser: SimBotVisualGroundingOutputParser,
        planner_type: SearchPlannerType = SearchPlannerType.greedy_max_vertex_cover,
        distance_threshold: float = 3,
        viewpoint_budget: int = 3,
        enable_grab_from_history: bool = True,
    ) -> "SimBotFindObjectPipeline":
        """Instantiate the pipeline from the SearchPlannerType."""
        planners = {
            SearchPlannerType.basic: BasicSearchPlanner(),
            SearchPlannerType.greedy_max_vertex_cover: GreedyMaximumVertexCoverSearchPlanner(
                distance_threshold=distance_threshold, vertex_budget=viewpoint_budget
            ),
        }

        return cls(
            features_client=features_client,
            action_predictor_client=action_predictor_client,
            visual_grounding_output_parser=visual_grounding_output_parser,
            search_planner=planners[planner_type],
            enable_grab_from_history=enable_grab_from_history,
        )

    def run(self, session: SimBotSession) -> Optional[SimBotAction]:  # noqa: WPS212
        """Handle the search through the environment."""
        if self._should_start_new_search(session):
            logger.debug("Preparing search plan...")
            with tracer.start_as_current_span("Building search plan"):
                search_plan = self._build_search_plan(session)

            # Reset the queue and counter and add the search plan
            session.current_state.find_queue.reset()
            session.current_state.find_queue.extend_tail(search_plan)
            # Reset the camera
            return self._get_next_action_from_plan(session)

        if self._should_reset_utterance_queue(session):
            logger.debug("Find queue is empty; returning None")
            self._search_planner.reset_utterance_queue_if_object_not_found(session)
            return None

        # If the next action is a dummy to reset the camera, execute it before searching
        if self._next_action_is_dummy(session):
            return session.current_state.find_queue.pop_from_head()

        if self._should_goto_found_object(session):
            goto_action = session.current_state.find_queue.pop_from_head()
            logger.warning("Clearing the find queue of the session")
            session.current_state.find_queue.reset()
            return goto_action

        extracted_features = self._features_client.get_features(session.current_turn)
        session.update_agent_memory(extracted_features)

        # Try to find the object in the previous turn
        try:
            decoded_scene_object_tokens = self._get_object_from_turn(session, extracted_features)
        except AssertionError:
            # If the object has not been found, get the next action to perform
            return self._get_next_action_from_plan(session)

        # If the object has been found, create the highlight and goto action, and return the
        # highlight
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
            # In practice this should never happen, if the searchable_object is not populated then this isnt a problem in the find pipeline
            if session.current_turn.intent.physical_interaction is None:
                return self._search_planner.run(session)

            searchable_object = session.current_turn.intent.physical_interaction.entity
            if searchable_object is None:
                return self._search_planner.run(session)

            current_room = session.current_turn.environment.current_room

            gfh_location = session.current_state.memory.read_memory_entity_in_room(
                room_name=current_room, object_label=searchable_object
            )

            if gfh_location is None:
                logger.debug(
                    f"Could not retrieve {searchable_object} from memory {session.current_state.memory}"
                )
                return self._search_planner.run(session)
            logger.debug(f"Found object {searchable_object} in location {gfh_location}")
            return self._search_planner.run(session, gfh_location=gfh_location)
        return self._search_planner.run(session)

    def _should_start_new_search(self, session: SimBotSession) -> bool:
        """Should we be starting a new search?

        If the queue is empty, start a new one. If the queue is not empty, do not.
        """
        return not session.is_find_object_in_progress

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
        head_action = session.current_state.find_queue.queue[0]
        return head_action.type == SimBotActionType.GotoObject

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
        )
        # Do not highlight objects when the intent is a search and no_match
        # Go straight to the object and execute the original instruction
        if session.current_turn.intent.is_searching_after_not_seeing_object:
            session.current_state.find_queue.reset()
            return goto_action
        # Add the goto action to the head of the queue
        session.current_state.find_queue.append_to_head(goto_action)
        logger.debug(f"Appending to head goto action {session.current_state.find_queue.queue[0]}")
        session.current_state.find_queue.append_to_head(self._search_planner.dummy_action())
        logger.debug(f"Appending to head dummy action {session.current_state.find_queue.queue[0]}")

        highlight_action = self._create_action_from_scene_object(
            action_type=SimBotActionType.Highlight,
            object_mask=object_mask,
            frame_index=scene_object_tokens.frame_index,
            object_index=scene_object_tokens.object_index,
            color_image_index=color_image_index,
        )
        return highlight_action

    def _create_action_from_scene_object(
        self,
        action_type: SimBotActionType,
        object_mask: SimBotObjectMaskType,
        frame_index: int,
        object_index: int,
        color_image_index: int,
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
                    # TODO: do we need an object name? What if we need the closest stickynote?
                    name="",
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
