from loguru import logger

from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN, PREDICTED_ACTION_DELIMITER
from emma_experience_hub.constants.simbot import ROOM_SYNONYNMS
from emma_experience_hub.datamodels.common import ArenaLocation
from emma_experience_hub.datamodels.simbot import (
    SimBotAction,
    SimBotActionType,
    SimBotIntent,
    SimBotIntentType,
    SimBotSession,
)
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotGotoPosition,
    SimBotGotoPositionPayload,
    SimBotGotoRoom,
    SimBotGotoRoomPayload,
)
from emma_experience_hub.functions.simbot.search import SearchPlanner


class GrabFromHistory:
    """Grab from History class."""

    def __call__(  # noqa: WPS212
        self,
        session: SimBotSession,
        search_planner: SearchPlanner,
    ) -> list[SimBotAction]:
        """Plan the actions needed to find an object for a given position."""
        # In practice this should never happen, if the searchable_object is not populated then this isnt a problem in the find pipeline
        if session.current_turn.intent.physical_interaction is None:
            return search_planner.run(session)

        searchable_object = session.current_turn.intent.physical_interaction.entity
        if searchable_object is None:
            return search_planner.run(session)

        current_room = session.current_turn.environment.current_room

        # Have we seen the object in the current room?
        gfh_location = session.current_state.memory.read_memory_entity_in_room(
            room_name=current_room, object_label=searchable_object
        )
        # If yes, start the search from that location
        if gfh_location is not None:
            logger.debug(f"Found object {searchable_object} in location {gfh_location}")
            if gfh_location == session.current_turn.environment.current_position:
                gfh_location = None
            return search_planner.run(session, gfh_location=gfh_location)

        # If we just moved to a new room, search there
        previous_turn = session.previous_valid_turn
        if previous_turn and previous_turn.actions.interaction.is_goto_room:
            return search_planner.run(session)

        #  Have we seen the object in a different room?
        gfh_other_room_locations = session.current_state.memory.read_memory_entity_in_arena(
            object_label=searchable_object
        )
        # If yes, confirm before going to the location
        if gfh_other_room_locations:
            logger.debug(
                f"Found object {searchable_object} in other room location {gfh_other_room_locations[0][0]}"
            )
            return self._confirm_location_in_different_room(
                session=session,
                searchable_object=searchable_object,
                gfh_other_room_location=gfh_other_room_locations[0],
            )

        #  Do we have prior knowledge about the room of the object?
        gfh_prior_memory_room = session.current_state.memory.read_prior_memory_entity_in_arena(
            object_label=searchable_object
        )
        # If prior knowlwedge says that the object is in the current room start searching
        if gfh_prior_memory_room == current_room:
            return search_planner.run(session)

        if gfh_prior_memory_room is not None:
            logger.debug(
                f"Found object {searchable_object} in prior memory room {gfh_prior_memory_room}"
            )
            return self._confirm_room_in_prior_memory(
                session=session, searchable_object=searchable_object, room=gfh_prior_memory_room
            )

        logger.debug(
            f"Could not retrieve {searchable_object} from memory {session.current_state.memory}"
        )
        return search_planner.run(session)

    def _confirm_location_in_different_room(
        self,
        session: SimBotSession,
        gfh_other_room_location: tuple[str, ArenaLocation],
        searchable_object: str,
    ) -> list[SimBotAction]:
        """Confirm before going to a room based on memory."""
        room = gfh_other_room_location[0]
        self._update_session(session=session, room=room, searchable_object=searchable_object)
        return [self._create_goto_position_action(gfh_other_room_location[1])]

    def _confirm_room_in_prior_memory(
        self, session: SimBotSession, room: str, searchable_object: str
    ) -> list[SimBotAction]:
        """Confirm before going to a room based on prior memory."""
        self._update_session(session=session, room=room, searchable_object=searchable_object)
        return [self._create_goto_room_action(room)]

    def _update_session(self, session: SimBotSession, room: str, searchable_object: str) -> None:
        """Update the session to confirm going to a different room."""
        room_name = ROOM_SYNONYNMS.get(room, room)
        if session.current_turn.speech is not None:
            utterance = session.current_turn.speech.utterance
        else:
            utterance = f"find the {searchable_object}"

        session.current_state.utterance_queue.append_to_head(utterance)
        session.current_turn.intent.verbal_interaction = SimBotIntent(
            type=SimBotIntentType.confirm_before_goto_room, entity=room_name
        )

    def _create_goto_room_action(self, room: str) -> SimBotAction:
        """Create action for going to a room."""
        return SimBotAction(
            id=0,
            type=SimBotActionType.GotoRoom,
            raw_output=f"goto {room} {END_OF_TRAJECTORY_TOKEN}{PREDICTED_ACTION_DELIMITER}",
            payload=SimBotGotoRoomPayload(object=SimBotGotoRoom(officeRoom=room)),
        )

    def _create_goto_position_action(self, location: ArenaLocation) -> SimBotAction:
        """Create action for going to a given position."""
        return SimBotAction(
            id=0,
            type=SimBotActionType.GotoPosition,
            raw_output=f"goto position {END_OF_TRAJECTORY_TOKEN}{PREDICTED_ACTION_DELIMITER}",
            payload=SimBotGotoPositionPayload(
                object=SimBotGotoPosition(position=location.position, rotation=location.rotation)
            ),
        )
