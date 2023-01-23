from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

import numpy as np
from loguru import logger
from numpy import typing

from emma_experience_hub.api.clients.simbot import (
    SimbotActionPredictionClient,
    SimBotFeaturesClient,
)
from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN, PREDICTED_ACTION_DELIMITER
from emma_experience_hub.datamodels.simbot import (
    SimBotAction,
    SimBotActionType,
    SimBotSession,
    SimBotSessionTurn,
)
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotGotoViewpoint,
    SimBotGotoViewpointPayload,
    SimBotRotatePayload,
)


class PlannerType(Enum):
    """Available planner types."""

    basic = "basic"
    greedy_max_vertex_cover = "greedy_max_vertex_cover"


class SearchPlanner(ABC):
    """Parent planner class."""

    def __init__(self, rotation_magnitude: float = 90):
        self.rotation_magnitude = rotation_magnitude

    @abstractmethod
    def run(self, session: SimBotSession) -> list[SimBotAction]:
        """Plan the actions needed to find an object for a given position."""
        raise NotImplementedError()

    def reset_utterance_queue_if_object_not_found(
        self, session: SimBotSession, current_action: Optional[SimBotAction] = None
    ) -> None:
        """Reset the utterance queue if the object was not found."""
        # The object was not found if the find queue is empty and
        if current_action is None:
            # there is no remaining action
            action_is_final = True
        else:
            # the remaining action is the final Rotate Left
            action_is_final = current_action.type == SimBotActionType.RotateLeft

        if not session.current_state.find_queue and action_is_final:
            session.current_state.utterance_queue.reset()

    def _create_goto_viewpoint_action(self, viewpoint_name: str) -> SimBotAction:
        """Create action for going to a view point."""
        return SimBotAction(
            id=0,
            type=SimBotActionType.GotoViewpoint,
            raw_output=f"goto {viewpoint_name}{PREDICTED_ACTION_DELIMITER}",
            payload=SimBotGotoViewpointPayload(
                object=SimBotGotoViewpoint(goToPoint=viewpoint_name)
            ),
        )

    def _create_turn_left_action(self, add_stop_token: bool = False) -> SimBotAction:
        """Create a turn left action."""
        if add_stop_token:
            raw_output = f"turn left {END_OF_TRAJECTORY_TOKEN}{PREDICTED_ACTION_DELIMITER}"
        else:
            raw_output = f"turn left{PREDICTED_ACTION_DELIMITER}"
        return SimBotAction(
            id=0,
            type=SimBotActionType.RotateLeft,
            raw_output=raw_output,
            payload=SimBotRotatePayload(direction="Left", magnitude=self.rotation_magnitude),
        )


class BasicSearchPlanner(SearchPlanner):
    """Basic search plan.

    Keep rotating from the current position.
    """

    def __init__(self, rotation_magnitude: float = 90):
        super().__init__(rotation_magnitude=rotation_magnitude)

    def run(self, session: SimBotSession) -> list[SimBotAction]:
        """Get the actions produced by the planner."""
        return self._create_look_around_actions()

    def _create_look_around_actions(self) -> list[SimBotAction]:
        """Create actions to perform the look around."""
        actions = [
            self._create_turn_left_action(),
            self._create_turn_left_action(),
            self._create_turn_left_action(),
            self._create_turn_left_action(add_stop_token=True),
        ]
        return actions


class GrabFromHistorySearchPlanner(BasicSearchPlanner):
    """Create a plan to go to the object if we've seen it before."""

    def __init__(
        self,
        features_client: SimBotFeaturesClient,
        action_predictor_client: SimbotActionPredictionClient,
        num_turns_to_search_through: int = 10,
        rotation_magnitude: int = 90,
    ) -> None:
        super().__init__(rotation_magnitude=rotation_magnitude)

        self._features_client = features_client
        self._action_predictor_client = action_predictor_client
        self._num_turns_to_search_through = num_turns_to_search_through

    def run(self, session: SimBotSession) -> list[SimBotAction]:
        """Go to the object if we have seen it before.

        If the entity cannot be found in the turns, an exception will be raised.
        """
        turn_with_entity = self._get_turn_with_entity(session)
        return self._build_plan(turn_with_entity)

    def _get_turns_to_search_through(self, session: SimBotSession) -> list[SimBotSessionTurn]:
        """Get the list of turns to search for the entity in."""
        return session.valid_turns[-self._num_turns_to_search_through :]

    def _get_turn_with_entity(self, session: SimBotSession) -> SimBotSessionTurn:
        """Get the turn where we previously saw the entity."""
        turns_to_search_through = self._get_turns_to_search_through(session)

        if not turns_to_search_through:
            raise AssertionError("[GFH] turns_to_search_through is empty. Skipping GFH")

        environment_state_history = session.get_environment_state_history_from_turns(
            turns_to_search_through, self._features_client.get_features
        )

        if not environment_state_history:
            raise AssertionError("[GFH] environment_state_history is empty. Skipping GFH")

        turn_index = self._action_predictor_client.find_entity_from_history(
            environment_state_history, session.current_turn.utterances
        )

        if turn_index is None:
            raise AssertionError("[GFH] Unable to find entity in turns")

        return turns_to_search_through[turn_index]

    def _build_plan(self, turn_with_entity: SimBotSessionTurn) -> list[SimBotAction]:
        """Build the plan to find the object."""
        viewpoint_name = turn_with_entity.environment.get_closest_viewpoint_name()

        goto_closest_viewpoint = self._create_goto_viewpoint_action(viewpoint_name)
        return [goto_closest_viewpoint, *self._create_look_around_actions()]


class GreedyMaximumVertexCoverSearchPlanner(BasicSearchPlanner):
    """Greedy maximum vertex cover search planner.

    Given a viewpoint budget, select the viewpoints that cover the largest area.
    """

    def __init__(
        self,
        distance_threshold: float = 3.0,
        vertex_budget: int = 2,
        use_current_position: bool = True,
        rotation_magnitude: float = 90,
    ) -> None:
        super().__init__(rotation_magnitude=rotation_magnitude)

        self.distance_threshold = distance_threshold
        self.viewpoint_budget = vertex_budget
        self.use_current_position = use_current_position

    def get_coverage_sets(self, coords: typing.NDArray[np.float64]) -> typing.NDArray[np.float64]:
        """Get the set of viewpoints covered by each other point."""
        # Fast pairwise euclidean distance instead of computing 1-by-1.
        pairwise_distances = np.sqrt(
            ((coords[:, :, None] - coords[:, :, None].T) ** 2).sum(1)  # noqa: WPS221
        )
        coverage_sets = np.array(pairwise_distances <= self.distance_threshold, dtype=int)
        return coverage_sets

    def select_based_on_maximum_coverage(
        self, coverage_sets: typing.NDArray[np.float64], first_selected_idx: Optional[int] = None
    ) -> list[int]:
        """Greedy algorithm for selecting the viewpoints resulting in maximum coverage.

        Can set the first_selected_idx to force the first vertex to be the index of the
        coverage_sets array. This can be used to ensure that the agent's position is always
        selected by the algorithm.
        """
        selected_viewpoints = []
        for iteration in range(self.viewpoint_budget):
            if np.all(coverage_sets.sum(1) == 0):
                break
            if iteration == 0 and first_selected_idx is not None:
                # Force selecting the robot position first
                # This ensures that we first look around from the current position of the robot before going to another viewpoint
                selected_idx = first_selected_idx
            else:
                # Select the next viewpoint that covers most others
                selected_idx = np.argmax(coverage_sets.sum(1), -1)
                selected_viewpoints.append(selected_idx)
            # Set to zero all viewpoints already covered
            coverage_sets[coverage_sets[selected_idx] > 0, :] = 0
            coverage_sets[:, coverage_sets[selected_idx] > 0] = 0

        logger.debug(f"[SEARCH] Number of selected viewpoints = {len(selected_viewpoints)}")
        logger.debug(
            f"[SEARCH] Number of viewpoints not covered = {np.where(coverage_sets.sum(0) > 0)[0].shape[0]}"
        )
        return selected_viewpoints

    def get_vertex_candidates(
        self, session: SimBotSession
    ) -> tuple[list[str], list[list[float]], Optional[int]]:
        """Get the vertex candidates for the current position.

        The candidates correspond to the viewpoints for the current room. If the
        use_current_position is set, the position of the agent at the present timestep is also
        added to the candidates.
        """
        environment = session.current_turn.environment
        current_position = environment.current_position
        current_room = environment.current_room

        name_candidates = []
        location_candidates = []
        first_selected_idx = None
        if self.use_current_position:
            location_candidates.append(current_position.as_list())
            first_selected_idx = 0

        for viewpoint, coords in environment.viewpoints.items():
            if viewpoint.startswith(current_room):
                name_candidates.append(viewpoint)
                location_candidates.append(coords.as_list())
        return name_candidates, location_candidates, first_selected_idx

    def get_actions_for_viewpoint(self) -> list[SimBotAction]:
        """Return the necessary actions needed to be done in a single viewpoint.

        We only need to rotate 3 times to see all the objects in a single viewpoint.
        """
        return self._create_look_around_actions()

    def run(self, session: SimBotSession) -> list[SimBotAction]:
        """Get the actions produced by the planner."""
        (name_candidates, location_candidates, first_selected_idx) = self.get_vertex_candidates(
            session
        )

        location_candidates_array = np.array(location_candidates)
        name_candidates_array = np.array(name_candidates)

        coverage_sets = self.get_coverage_sets(location_candidates_array)
        # Select the maximum coverage location, force the first one to be the robot location
        selected_room_locations = self.select_based_on_maximum_coverage(
            coverage_sets, first_selected_idx=first_selected_idx
        )
        # We need 3 turns for each planned location + 1 more for the last viewpoint
        planned_actions = self.get_actions_for_viewpoint()
        if selected_room_locations:
            for name in name_candidates_array[selected_room_locations]:
                planned_actions.append(self._create_goto_viewpoint_action(name))
                planned_actions.extend(self.get_actions_for_viewpoint())

        planned_actions.append(self._create_turn_left_action(add_stop_token=True))
        logger.debug(f"[SEARCH] Plan = {planned_actions}")
        return planned_actions

    def _create_look_around_actions(self) -> list[SimBotAction]:
        """Create actions to perform the look around."""
        actions = [
            self._create_turn_left_action(),
            self._create_turn_left_action(),
            self._create_turn_left_action(),
        ]

        return actions
