from loguru import logger

from emma_common.datamodels import SpeakerRole
from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN, PREDICTED_ACTION_DELIMITER
from emma_experience_hub.constants.simbot import ROOM_SYNONYNMS
from emma_experience_hub.datamodels.simbot import SimBotIntent, SimBotIntentType, SimBotSession
from emma_experience_hub.datamodels.simbot.actions import SimBotAction
from emma_experience_hub.datamodels.simbot.enums import SimBotActionType
from emma_experience_hub.datamodels.simbot.payloads import SimBotGotoRoom, SimBotGotoRoomPayload
from emma_experience_hub.datamodels.simbot.queue import SimBotQueueUtterance
from emma_experience_hub.functions.simbot.search import SearchPlanner


class GrabFromHistory:
    """Grab from History class."""

    def __call__(
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

        return search_planner.run(session)

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

    def _ask_for_confirmation_before_search(
        self, session: SimBotSession, room: str, searchable_object: str
    ) -> list[SimBotAction]:
        """Ask confirmation before moving to the correct room based on prior memory."""
        if session.current_turn.speech is not None:
            utterance = session.current_turn.speech.utterance
            role = session.current_turn.speech.role
        else:
            utterance = f"find the {searchable_object}"
            role = SpeakerRole.agent

        session.current_state.utterance_queue.append_to_head(
            SimBotQueueUtterance(utterance=utterance, role=role),
        )
        queue_elem = SimBotQueueUtterance(
            utterance=f"go to the {ROOM_SYNONYNMS[room]}",
            role=SpeakerRole.agent,
        )
        session.current_state.utterance_queue.append_to_head(queue_elem)
        session.current_turn.intent.verbal_interaction = SimBotIntent(
            type=SimBotIntentType.confirm_before_plan, entity=room
        )
        return []

    def _create_goto_room_action(self, room: str) -> SimBotAction:
        """Create action for going to a room."""
        return SimBotAction(
            id=0,
            type=SimBotActionType.GotoRoom,
            raw_output=f"goto {room} {END_OF_TRAJECTORY_TOKEN}{PREDICTED_ACTION_DELIMITER}",
            payload=SimBotGotoRoomPayload(object=SimBotGotoRoom(officeRoom=room)),
        )
