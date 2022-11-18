from contextlib import suppress

from loguru import logger

from emma_experience_hub.api.clients.simbot import SimBotSessionDbClient
from emma_experience_hub.datamodels.simbot import (
    SimBotActionStatus,
    SimBotRequest,
    SimBotSession,
    SimBotSessionTurn,
)


class SimBotRequestProcessingPipeline:
    """Process the incoming requests and build the session data."""

    def __init__(self, session_db_client: SimBotSessionDbClient) -> None:
        self._session_db_client = session_db_client

    def run(self, request: SimBotRequest) -> SimBotSession:
        """Run the pipeline for the current request."""
        # Get all the previous turns for the history
        session_history = self.get_session_history(request.header.session_id)

        if session_history:
            self.update_previous_turn_with_action_status(
                session_history[-1], request.request.previous_actions
            )

        # Create a turn for the current request and update the history
        session_history.append(
            SimBotSessionTurn.new_from_simbot_request(request, idx=len(session_history))
        )

        # Instantiate the session from the turns
        session = SimBotSession(session_id=request.header.session_id, turns=session_history)

        # Set the state of the current turn to be the same as the previous turn, since that is
        # where we start from.
        if session.previous_turn:
            session.current_turn.state = session.previous_turn.state.copy(deep=True)

        return session

    def get_session_history(self, session_id: str) -> list[SimBotSessionTurn]:
        """Get the history for the session.

        This should use an API client to pull the history for the given session.
        """
        return self._session_db_client.get_all_session_turns(session_id)

    def update_previous_turn_with_action_status(
        self, turn: SimBotSessionTurn, action_status: list[SimBotActionStatus]
    ) -> None:
        """Update the previous turn with the action status.

        We are assuming that the order of actions is the exact same as the order of action
        statuses.
        """
        if not action_status:
            logger.warning(
                "Previous action status is empty, therefore cannot update status of previous session turn. Moving on..."
            )
            return

        if len(action_status) != len(turn.actions):
            logger.error(
                f"The number of actions with the turn is not equal to the number of statuses available. There are {len(turn.actions)} actions within the turn, but {len(action_status)} statuses."
            )
            logger.warning(
                "Trying to match the available actions to the available statuses anyway."
            )

        # Update the action status, ensuring we match the right one.
        action_status_id_map = {status.id: status for status in action_status}

        with suppress(KeyError):
            for action in turn.actions:
                if action.id is not None:
                    action.status = action_status_id_map[action.id]

        # Put the updated session turn into the db
        self._session_db_client.put_session_turn(turn)
