from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

import numpy as np
from loguru import logger
from numpy import typing

from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN, PREDICTED_ACTION_DELIMITER
from emma_experience_hub.datamodels.simbot import SimBotAction, SimBotActionType, SimBotSession
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

    @abstractmethod
    def run(self, session: SimBotSession) -> list[SimBotAction]:
        """Plan the actions needed to find an object for a given position."""
        raise NotImplementedError()


class BasicSearchPlanner(SearchPlanner):
    """Basic search plan.

    Keep rotating from the current position.
    """

    def __init__(self, rotation_magnitude: float = 90):
        self.rotation_magnitude = rotation_magnitude

    def run(self, session: SimBotSession) -> list[SimBotAction]:
        """Get the actions produced by the planner."""
        return [
            SimBotAction(
                id=0,
                type=SimBotActionType.RotateLeft,
                raw_output=f"turn left{PREDICTED_ACTION_DELIMITER}",
                payload=SimBotRotatePayload(direction="Left", magnitude=self.rotation_magnitude),
            ),
            SimBotAction(
                id=0,
                type=SimBotActionType.RotateLeft,
                raw_output=f"turn left{PREDICTED_ACTION_DELIMITER}",
                payload=SimBotRotatePayload(direction="Left", magnitude=self.rotation_magnitude),
            ),
            SimBotAction(
                id=0,
                type=SimBotActionType.RotateLeft,
                raw_output=f"turn left{PREDICTED_ACTION_DELIMITER}",
                payload=SimBotRotatePayload(direction="Left", magnitude=self.rotation_magnitude),
            ),
            SimBotAction(
                id=0,
                type=SimBotActionType.RotateLeft,
                raw_output=f"turn left {END_OF_TRAJECTORY_TOKEN}{PREDICTED_ACTION_DELIMITER}",
                payload=SimBotRotatePayload(direction="Left", magnitude=self.rotation_magnitude),
            ),
        ]


class GreedyMaximumVertexCoverSearchPlanner(SearchPlanner):
    """Greedy maximum vertex cover search planner.

    Given a viewpoint budget, select the viewpoints that cover the largest area.
    """

    def __init__(
        self,
        distance_threshold: float = 2,
        vertex_budget: int = 2,
        use_current_position: bool = True,
        rotation_magnitude: float = 90,
    ):
        self.distance_threshold = distance_threshold
        self.viewpoint_budget = vertex_budget
        self.use_current_position = use_current_position
        self.rotation_magnitude = rotation_magnitude

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

        logger.debug(f"Number of selected viewpoints = {len(selected_viewpoints)}")
        logger.debug(
            f"Number of viewpoints not covered = {np.where(coverage_sets.sum(0) > 0)[0].shape[0]}"
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
        return [
            SimBotAction(
                id=0,
                type=SimBotActionType.RotateLeft,
                raw_output=f"turn left{PREDICTED_ACTION_DELIMITER}",
                payload=SimBotRotatePayload(direction="Left", magnitude=self.rotation_magnitude),
            ),
            SimBotAction(
                id=0,
                type=SimBotActionType.RotateLeft,
                raw_output=f"turn left{PREDICTED_ACTION_DELIMITER}",
                payload=SimBotRotatePayload(direction="Left", magnitude=self.rotation_magnitude),
            ),
            SimBotAction(
                id=0,
                type=SimBotActionType.RotateLeft,
                raw_output=f"turn left{PREDICTED_ACTION_DELIMITER}",
                payload=SimBotRotatePayload(direction="Left", magnitude=self.rotation_magnitude),
            ),
        ]

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
        planned_actions = []
        if selected_room_locations:
            for name in name_candidates_array[selected_room_locations]:
                actions_for_viewpoint = self.get_actions_for_viewpoint()

                actions_for_viewpoint.append(
                    SimBotAction(
                        id=0,
                        type=SimBotActionType.GotoViewpoint,
                        raw_output=f"goto {name}.",
                        payload=SimBotGotoViewpointPayload(
                            object=SimBotGotoViewpoint(goToPoint=name)
                        ),
                    ),
                )
                planned_actions.extend(actions_for_viewpoint)

        # We need 1 look around for each planned location + 1 more for the current viewpoint
        planned_actions.extend(self.get_actions_for_viewpoint())
        return planned_actions
