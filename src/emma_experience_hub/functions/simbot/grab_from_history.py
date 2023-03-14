from loguru import logger

from emma_common.datamodels import SpeakerRole
from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN, PREDICTED_ACTION_DELIMITER
from emma_experience_hub.datamodels.simbot import SimBotSession
from emma_experience_hub.datamodels.simbot.actions import SimBotAction
from emma_experience_hub.datamodels.simbot.enums import SimBotActionType
from emma_experience_hub.datamodels.simbot.payloads import SimBotGotoRoom, SimBotGotoRoomPayload
from emma_experience_hub.datamodels.simbot.queue import SimBotQueueUtterance
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

        # Is it an object we should search in different rooms?
        gfh_prior_memory_room = session.current_state.memory.read_prior_memory_entity_in_arena(
            object_label=searchable_object
        )
        if gfh_prior_memory_room is None:
            logger.debug(
                f"Could not retrieve {searchable_object} from memory {session.current_state.memory}"
            )
            return search_planner.run(session)
        # If prior knowlwedge says that the object is in the current room start searching
        if gfh_prior_memory_room == current_room:
            return search_planner.run(session)

        # Otherwise, just go to the room
        logger.debug(
            f"Found object {searchable_object} in prior memory room {gfh_prior_memory_room}"
        )
        return self._goto_room_before_search(
            session=session, searchable_object=searchable_object, room=gfh_prior_memory_room
        )

    def _goto_room_before_search(
        self, session: SimBotSession, room: str, searchable_object: str
    ) -> list[SimBotAction]:
        """Move to the correct room based on prior memory."""
        if session.current_turn.speech is not None:
            utterance = session.current_turn.speech.utterance
            role = session.current_turn.speech.role
        else:
            utterance = f"find the {searchable_object}"
            role = SpeakerRole.agent

        session.current_state.utterance_queue.append_to_head(
            SimBotQueueUtterance(utterance=utterance, role=role),
        )
        return [self._create_goto_room_action(room)]

    def _create_goto_room_action(self, room: str) -> SimBotAction:
        """Create action for going to a room."""
        return SimBotAction(
            id=0,
            type=SimBotActionType.GotoRoom,
            raw_output=f"goto {room} {END_OF_TRAJECTORY_TOKEN}{PREDICTED_ACTION_DELIMITER}",
            payload=SimBotGotoRoomPayload(object=SimBotGotoRoom(officeRoom=room)),
        )
