from emma_experience_hub.datamodels.simbot import SimBotAction, SimBotSession
from emma_experience_hub.parsers.parser import Parser


class SimBotPreviousActionParser(Parser[SimBotSession, SimBotAction]):
    """Get the previous interation action from the session for the current turn.

    This parser is most useful when handling approved confirmation requests.
    """

    def __call__(self, session: SimBotSession) -> SimBotAction:
        """Get the action from the previous turn."""
        # Get the interaction action from the previous turn
        previous_interaction_action = self._get_previous_interaction_action(session)

        return previous_interaction_action

    def _get_previous_interaction_action(self, session: SimBotSession) -> SimBotAction:
        """Get the interaction action from the previous turn."""
        if not session.previous_valid_turn:
            raise AssertionError("There is no previous turn to get the action from.")

        if not session.previous_valid_turn.actions.interaction:
            raise AssertionError("There is no interaction action in the previous valid turn")

        return session.previous_valid_turn.actions.interaction
