from typing import Optional

from loguru import logger
from opentelemetry import trace

from emma_experience_hub.api.clients.simbot import (
    SimbotActionPredictionClient,
    SimBotFeaturesClient,
)
from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN, PREDICTED_ACTION_DELIMITER
from emma_experience_hub.datamodels import EmmaExtractedFeatures, EnvironmentStateTurn
from emma_experience_hub.datamodels.enums import SearchPlannerType
from emma_experience_hub.datamodels.simbot import SimBotAction, SimBotActionType, SimBotSession
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotInteractionObject,
    SimBotObjectInteractionPayload,
    SimBotObjectMaskType,
)
from emma_experience_hub.functions.simbot import (
    BasicSearchPlanner,
    GrabFromHistorySearchPlanner,
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
        grab_from_history_search_planner: SearchPlanner,
        _enable_grab_from_history: bool = True,
    ) -> None:
        self._features_client = features_client

        self._action_predictor_client = action_predictor_client
        self._visual_grounding_output_parser = visual_grounding_output_parser

        self._search_planner = search_planner
        self._grab_from_history_search_planner = grab_from_history_search_planner
        self._enable_grab_from_history = _enable_grab_from_history

    @classmethod
    def from_planner_type(
        cls,
        features_client: SimBotFeaturesClient,
        action_predictor_client: SimbotActionPredictionClient,
        visual_grounding_output_parser: SimBotVisualGroundingOutputParser,
        planner_type: SearchPlannerType = SearchPlannerType.greedy_max_vertex_cover,
        distance_threshold: float = 3,
        viewpoint_budget: int = 3,
        _enable_grab_from_history: bool = True,
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
            grab_from_history_search_planner=GrabFromHistorySearchPlanner(
                features_client, action_predictor_client
            ),
            _enable_grab_from_history=_enable_grab_from_history,
        )

    def run(self, session: SimBotSession) -> Optional[SimBotAction]:
        """Handle the search through the environment."""
        if self._should_start_new_search(session):
            logger.debug("Preparing search plan...")
            with tracer.start_as_current_span("Building search plan"):
                search_plan = self._build_search_plan(session)

            # Reset the queue and counter and add the search plan
            session.current_state.find_queue.reset()
            session.current_state.find_queue.extend_tail(search_plan)

        if self._should_goto_found_object(session):
            # Pop the gotoaction from the head and clear the plan.
            goto_action = session.current_state.find_queue.pop_from_head()
            logger.warning("Clearing the find queue of the session")
            session.current_state.find_queue.reset()
            return goto_action

        if not session.current_state.find_queue:
            logger.debug("Find queue is empty; returning None")
            self._search_planner.reset_utterance_queue_if_object_not_found(session)
            return None

        extracted_features = self._features_client.get_features(session.current_turn)

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

    def _build_search_plan(self, session: SimBotSession) -> list[SimBotAction]:
        """Build a plan of actions for the current session."""
        if self._enable_grab_from_history:
            try:
                return self._grab_from_history_search_planner.run(session)
            except AssertionError:
                logger.info("Assertion Error. Failed to find object from history")
            except Exception as err:
                logger.exception("GFH failed", exc_info=err)
        return self._search_planner.run(session)

    def _should_start_new_search(self, session: SimBotSession) -> bool:
        """Should we be starting a new search?

        If the queue is empty, start a new one. If the queue is not empty, do not.
        """
        return not session.is_find_object_in_progress

    def _should_goto_found_object(self, session: SimBotSession) -> bool:
        """Should we go to the highlighted object?

        The queue contain has a goto action at its head whenever we have found an object.
        """
        head_action = session.current_state.find_queue.queue[0]
        return head_action.type == SimBotActionType.GotoObject

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
            session.get_turns_within_interaction_window(), include_agent_responses=False
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
        self._search_planner.reset_utterance_queue_if_object_not_found(session, next_action)
        return next_action
