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
        session_turn = SimBotSessionTurn.new_from_simbot_request(request, idx=len(session_history))
        session_history.append(session_turn)
        logger.debug(f"Created session turn: {session_turn}")

        # Instantiate the session from the turns
        session = SimBotSession(session_id=request.header.session_id, turns=session_history)

        # Set the state of the current turn to be the same as the previous turn, since that is
        # where we start from.
        if session.previous_turn:
            session.current_turn.state = session.previous_turn.state.copy(deep=True)

            # Check whether or not the agent inventory needs updating
            session.try_to_update_agent_inventory()

        logger.debug(f"Current turn: {session.current_turn}")

        if session_turn != session.current_turn:
            logger.error(
                "The current turn is not equal to the newly created session turn. The inference is likely about to go very wrong."
            )

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

        If we do not receive an action status for the entire turn, then we must assume that all
        previous actions completed successfully.
        """
        # If the previous turn did NOT end is a lightweight dialog action And there is no action
        # status, then assume all the actions completed successfully
        if not action_status:
            if turn.actions.dialog and not turn.actions.dialog.is_lightweight_dialog:
                turn.actions.mark_all_as_successful()

        # Update the action status, ensuring we match the right one.
        action_status_id_map = {status.id: status for status in action_status}
        with suppress(KeyError):
            for action in turn.actions:
                if action.id is not None:
                    action.status = action_status_id_map[action.id]

        # If there are errors, mark any actions without statuses as blocked
        if turn.actions.any_action_failed:
            turn.actions.mark_remaining_as_blocked()
        else:
            # If there are no errors in the actions, then mark the rest as successful
            turn.actions.mark_all_as_successful()

        # Put the updated session turn into the db
        self._session_db_client.put_session_turn(turn)
