import numpy as np
from loguru import logger
from numpy import typing

from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN, PREDICTED_ACTION_DELIMITER
from emma_experience_hub.datamodels.simbot import SimBotAction, SimBotActionType, SimBotSession
from emma_experience_hub.datamodels.simbot.enums import SimBotDummyRawActions
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotGotoViewpoint,
    SimBotGotoViewpointPayload,
)
from emma_experience_hub.functions.coordinates import get_closest_position_index_to_reference


class ViewpointPlanner:
    """Iterate over the viewpoints."""

    def __call__(self, session: SimBotSession, raw_action_output: str) -> SimBotAction:
        """Find the next position for a given position."""
        if raw_action_output.startswith(SimBotDummyRawActions.DummyNextViewpoint.value):
            return self._get_next_viewpoint_action(session)
        return self._get_previous_viewpoint_action(session)

    def _get_distance_from_first_viewpoint(
        self, coords: typing.NDArray[np.float64]
    ) -> typing.NDArray[np.float64]:
        """Get the distances from the first viewpoint."""
        return ((coords[0] - coords) ** 2).sum(1)

    def _sort_viewpoints_by_distance(
        self, viewpoint_coords: typing.NDArray[np.float64], viewpoint_names: list[str]
    ) -> list[str]:
        """Sort the viewpoints by distance from the current position."""
        distances = self._get_distance_from_first_viewpoint(viewpoint_coords)
        return [viewpoint_names[index] for index in distances.argsort()]

    def _get_room_viewpoints(
        self, session: SimBotSession
    ) -> tuple[list[str], typing.NDArray[np.float64]]:
        """Get the viewpoints in the current room sorted alphabetically."""
        # Get the viewpoints in the current room
        room_viewpoints = session.current_turn.environment.viewpoints_in_current_room
        viewpoint_names = list(room_viewpoints.keys())
        viewpoint_locations = list(room_viewpoints.values())

        # Sort the viewpoints by name
        indices = np.argsort(viewpoint_names)
        sorted_viewpoint_names = [viewpoint_names[index] for index in indices]
        sorted_viewpoint_locations = np.array(
            [viewpoint_locations[index].as_list() for index in indices]
        )
        return sorted_viewpoint_names, sorted_viewpoint_locations

    def _create_goto_viewpoint_action(self, viewpoint_name: str) -> SimBotAction:
        """Create action for going to a view point."""
        return SimBotAction(
            id=0,
            type=SimBotActionType.GotoViewpoint,
            raw_output=f"goto {viewpoint_name}{PREDICTED_ACTION_DELIMITER}{END_OF_TRAJECTORY_TOKEN}",
            payload=SimBotGotoViewpointPayload(
                object=SimBotGotoViewpoint(goToPoint=viewpoint_name)
            ),
        )

    def _get_viewpoint_closest_to_location(self, session: SimBotSession) -> str:
        """Get the name of the viewpoint closest to the current position."""
        environment = session.current_turn.environment
        current_position = environment.current_position
        viewpoints_in_current_room = environment.viewpoints_in_current_room
        viewpoint_index = get_closest_position_index_to_reference(
            current_position, viewpoints_in_current_room.values()
        )
        # Use the index to get the name of the viewpoint
        viewpoint_name = list(viewpoints_in_current_room.keys())[viewpoint_index]
        return viewpoint_name

    def _get_next_viewpoint_action(self, session: SimBotSession) -> SimBotAction:
        """Get the actions produced by the planner."""
        (name_candidates, location_candidates) = self._get_room_viewpoints(session)

        sorted_name_candidates = self._sort_viewpoints_by_distance(
            location_candidates, name_candidates
        )

        logger.info(f"[VIEWPOINT PLANNER] Sorted viewpoints: {sorted_name_candidates}")
        # Get the closest viewpoint to the current position
        closest_viewpoint = self._get_viewpoint_closest_to_location(session)
        closest_index = sorted_name_candidates.index(closest_viewpoint)
        # Get the next viewpoint
        if closest_index == len(sorted_name_candidates) - 1:
            # If the closest viewpoint is the last one, go to the first one
            return self._create_goto_viewpoint_action(sorted_name_candidates[0])
        return self._create_goto_viewpoint_action(sorted_name_candidates[closest_index + 1])

    def _get_previous_viewpoint_action(self, session: SimBotSession) -> SimBotAction:
        """Get the actions produced by the planner."""
        (name_candidates, location_candidates) = self._get_room_viewpoints(session)

        sorted_name_candidates = self._sort_viewpoints_by_distance(
            location_candidates, name_candidates
        )
        logger.info(f"[VIEWPOINT PLANNER] Sorted viewpoints: {sorted_name_candidates}")

        # Get the closest viewpoint to the current position
        closest_viewpoint = self._get_viewpoint_closest_to_location(session)
        closest_index = sorted_name_candidates.index(closest_viewpoint)
        # Get the previous viewpoint
        return self._create_goto_viewpoint_action(sorted_name_candidates[closest_index - 1])
