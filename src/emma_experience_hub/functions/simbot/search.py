from abc import ABC, abstractmethod
from typing import Optional, Union

import numpy as np
from loguru import logger
from numpy import typing

from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN, PREDICTED_ACTION_DELIMITER
from emma_experience_hub.constants.simbot import get_search_budget
from emma_experience_hub.datamodels.common import ArenaLocation, GFHLocationType
from emma_experience_hub.datamodels.simbot import SimBotAction, SimBotActionType, SimBotSession
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotGotoPosition,
    SimBotGotoPositionPayload,
    SimBotGotoViewpoint,
    SimBotGotoViewpointPayload,
    SimBotLookAroundPayload,
    SimBotMoveForwardPayload,
    SimBotRotatePayload,
)
from emma_experience_hub.functions.coordinates import get_closest_position_index_to_reference


class SearchPlanner(ABC):
    """Parent planner class."""

    def __init__(self, rotation_magnitude: float = 90):
        self.rotation_magnitude = rotation_magnitude

    @abstractmethod
    def run(
        self,
        session: SimBotSession,
        gfh_location: Optional[ArenaLocation] = None,
    ) -> list[SimBotAction]:
        """Plan the actions needed to find an object for a given position."""
        raise NotImplementedError()

    def reset_utterance_queue_if_object_not_found(
        self, session: SimBotSession, current_action: Optional[SimBotAction] = None
    ) -> None:
        """Reset the utterance queue if the object was not found."""
        # The object was not found if the find queue is empty and
        action_is_final = (
            # there is no remaining action
            current_action is None
            # the remaining action ends with the end of trajectory token
            or current_action.is_end_of_trajectory
        )

        if not session.current_state.find_queue and action_is_final:
            session.current_state.utterance_queue.reset()

    def dummy_action(self) -> SimBotAction:
        """Get a dummy action."""
        return self._create_dummy_action()

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

    def _create_goto_arena_location_action(self, location: ArenaLocation) -> SimBotAction:
        """Create action for going to a given position."""
        return SimBotAction(
            id=0,
            type=SimBotActionType.GotoPosition,
            raw_output=f"goto position{PREDICTED_ACTION_DELIMITER}",
            payload=SimBotGotoPositionPayload(
                object=SimBotGotoPosition(position=location.position, rotation=location.rotation)
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

    def _create_look_around_action(self, add_stop_token: bool = True) -> SimBotAction:
        """Create a look around action."""
        if add_stop_token:
            raw_output = f"look around {END_OF_TRAJECTORY_TOKEN}{PREDICTED_ACTION_DELIMITER}"
        else:
            raw_output = f"look around{PREDICTED_ACTION_DELIMITER}"
        return SimBotAction(
            id=0,
            type=SimBotActionType.LookAround,
            raw_output=raw_output,
            payload=SimBotLookAroundPayload(),
        )

    def _create_dummy_action(self) -> SimBotAction:
        """Dummy move forward action."""
        raw_output = f"move forward{PREDICTED_ACTION_DELIMITER}"
        return SimBotAction(
            id=0,
            type=SimBotActionType.MoveForward,
            raw_output=raw_output,
            payload=SimBotMoveForwardPayload(magnitude=0),
        )


class BasicSearchPlanner(SearchPlanner):
    """Basic search plan.

    Keep rotating from the current position.
    """

    def __init__(self, rotation_magnitude: float = 90):
        super().__init__(rotation_magnitude=rotation_magnitude)

    def run(
        self,
        session: SimBotSession,
        gfh_location: Optional[ArenaLocation] = None,
    ) -> list[SimBotAction]:
        """Get the actions produced by the planner."""
        # For search and no match, do a Look Around
        if session.current_turn.intent.is_searching_inferred_object:
            return [self._create_look_around_action()]
        return self._create_rotation_actions()

    def _create_rotation_actions(self) -> list[SimBotAction]:
        """Create actions to perform the look around."""
        actions = [
            self._create_turn_left_action(),
            self._create_turn_left_action(),
            self._create_turn_left_action(),
            self._create_turn_left_action(add_stop_token=True),
        ]
        return actions


class GreedyMaximumVertexCoverSearchPlanner(BasicSearchPlanner):
    """Greedy maximum vertex cover search planner.

    Given a viewpoint budget, select the viewpoints that cover the largest area.
    """

    def __init__(
        self,
        use_current_position: bool = True,
        rotation_magnitude: float = 90,
        gfh_location_type: GFHLocationType = GFHLocationType.location,
    ) -> None:
        super().__init__(rotation_magnitude=rotation_magnitude)
        self.search_budget = get_search_budget()
        self.use_current_position = use_current_position
        self.gfh_location_type = gfh_location_type

    def get_coverage_sets(
        self, coords: typing.NDArray[np.float64], current_room: str
    ) -> typing.NDArray[np.float64]:
        """Get the set of viewpoints covered by each other point."""
        # Fast pairwise euclidean distance instead of computing 1-by-1.
        pairwise_distances = np.sqrt(
            ((coords[:, :, None] - coords[:, :, None].T) ** 2).sum(1)  # noqa: WPS221
        )
        coverage_sets = np.array(
            pairwise_distances <= self.search_budget[current_room].distance_threshold, dtype=int
        )
        return coverage_sets

    def select_based_on_maximum_coverage(
        self,
        coverage_sets: typing.NDArray[np.float64],
        current_room: str,
        first_selected_idx: Optional[int] = None,
    ) -> list[int]:
        """Greedy algorithm for selecting the viewpoints resulting in maximum coverage.

        Can set the first_selected_idx to force the first vertex to be the index of the
        coverage_sets array. This can be used to ensure that the agent's position is always
        selected by the algorithm.
        """
        selected_viewpoints = []
        for iteration in range(self.search_budget[current_room].viewpoint_budget):
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
            name_candidates.append("current_position")
            location_candidates.append(current_position.as_list())
            first_selected_idx = 0

        for viewpoint, coords in environment.viewpoints.items():
            if viewpoint.startswith(current_room):
                name_candidates.append(viewpoint)
                location_candidates.append(coords.as_list())
        return name_candidates, location_candidates, first_selected_idx

    def add_gfh_location_to_vertex_candidates(
        self,
        name_candidates: list[str],
        location_candidates: list[list[float]],
        gfh_location: Union[ArenaLocation, str],
    ) -> tuple[list[str], list[list[float]], int]:
        """Update the vertex candidates with the GFH position."""
        if isinstance(gfh_location, ArenaLocation):
            name_candidates.append("gfh_location")
            location_candidates.append(gfh_location.position.as_list())
            name_candidates, location_candidates = self._remove_current_position_from_candidates(
                name_candidates, location_candidates
            )
            first_selected_idx = name_candidates.index("gfh_location")
        elif isinstance(gfh_location, str):
            name_candidates, location_candidates = self._remove_current_position_from_candidates(
                name_candidates, location_candidates
            )
            first_selected_idx = name_candidates.index(gfh_location)
        else:
            raise AssertionError(
                "GFH location should be a viewpoint name (str) or an Arena Location."
            )

        return name_candidates, location_candidates, first_selected_idx

    def get_actions_for_position(
        self,
        location_from_gfh: bool = False,
    ) -> list[SimBotAction]:
        """Return the necessary actions needed to be done in a single viewpoint."""
        return self._create_rotation_actions()

    def run(
        self,
        session: SimBotSession,
        gfh_location: Optional[ArenaLocation] = None,
    ) -> list[SimBotAction]:
        """Get the actions produced by the planner."""
        current_room = session.current_turn.environment.current_room
        (name_candidates, location_candidates, first_selected_idx) = self.get_vertex_candidates(
            session
        )
        first_location_from_gfh = False
        planned_actions: list[SimBotAction] = []
        if gfh_location is not None:
            first_location_from_gfh = True
            gfh_starting_location = self._get_gfh_starting_location(
                session=session,
                gfh_location=gfh_location,
                planned_actions=planned_actions,
            )
            (
                name_candidates,
                location_candidates,
                first_selected_idx,
            ) = self.add_gfh_location_to_vertex_candidates(
                name_candidates, location_candidates, gfh_starting_location
            )

        # We need 3 turns for each planned location + 1 more for the last viewpoint
        planned_actions.extend(
            self.get_actions_for_position(location_from_gfh=first_location_from_gfh)
        )
        location_candidates_array = np.array(location_candidates)
        name_candidates_array = np.array(name_candidates)

        coverage_sets = self.get_coverage_sets(
            location_candidates_array, current_room=current_room
        )
        # Select the maximum coverage location, force the first one to be the robot location
        selected_room_locations = self.select_based_on_maximum_coverage(
            coverage_sets, current_room=current_room, first_selected_idx=first_selected_idx
        )
        if selected_room_locations:
            for name in name_candidates_array[selected_room_locations]:
                planned_actions.append(self._create_goto_viewpoint_action(name))
                planned_actions.extend(self.get_actions_for_position())

        planned_actions.append(self._create_turn_left_action(add_stop_token=True))

        logger.debug(f"[SEARCH] Plan = {planned_actions}")
        return planned_actions

    def _create_rotation_actions(self) -> list[SimBotAction]:
        """Create actions to perform the look around."""
        actions = [
            self._create_turn_left_action(),
            self._create_turn_left_action(),
            self._create_turn_left_action(),
        ]

        return actions

    def _planned_actions_should_end_with_rotation(
        self, planned_actions: list[SimBotAction]
    ) -> bool:
        """Does the agent need to rotate left if the object is not found?

        If the last action is a rotate left and the object was not found, do a final rotation to
        end in the original position.
        """
        return planned_actions[-1].type == SimBotActionType.RotateLeft

    def _get_viewpoint_closest_to_location(
        self, gfh_location: ArenaLocation, session: SimBotSession
    ) -> str:
        viewpoints_in_current_room = session.current_turn.environment.viewpoints_in_current_room
        viewpoint_index = get_closest_position_index_to_reference(
            gfh_location.position, viewpoints_in_current_room.values()
        )
        # Use the index to get the name of the viewpoint
        viewpoint_name = list(viewpoints_in_current_room.keys())[viewpoint_index]
        return viewpoint_name

    def _get_gfh_starting_location(
        self,
        gfh_location: ArenaLocation,
        session: SimBotSession,
        planned_actions: list[SimBotAction],
    ) -> Union[ArenaLocation, str]:
        if self.gfh_location_type == GFHLocationType.location:
            planned_actions.append(self._create_goto_arena_location_action(gfh_location))
            return gfh_location

        gfh_viewpoint = self._get_viewpoint_closest_to_location(gfh_location, session)
        planned_actions.append(self._create_goto_viewpoint_action(gfh_viewpoint))
        return gfh_viewpoint

    def _remove_current_position_from_candidates(
        self, name_candidates: list[str], location_candidates: list[list[float]]
    ) -> tuple[list[str], list[list[float]]]:
        """Remove the current position from the candidates when the first position is from GFH."""
        if "current_position" in name_candidates:
            current_pos_index = name_candidates.index("current_position")
            name_candidates.pop(current_pos_index)
            location_candidates.pop(current_pos_index)
        return name_candidates, location_candidates
