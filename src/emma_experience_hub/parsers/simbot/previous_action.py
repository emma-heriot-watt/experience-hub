from typing import cast

from loguru import logger

from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN, PREDICTED_ACTION_DELIMITER
from emma_experience_hub.datamodels.simbot import SimBotAction, SimBotActionType, SimBotSession
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotGotoObject,
    SimBotGotoPayload,
    SimBotObjectInteractionPayload,
)
from emma_experience_hub.functions.simbot import SimBotDeconstructedAction
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

    def convert_action_to_goto_action(self, action: SimBotAction) -> SimBotAction:
        """Convert the action from the previous step into a Goto action."""
        # Ensure that we can get the payload from the action
        if not isinstance(action.payload, SimBotObjectInteractionPayload):
            logger.warning(
                "Cannot convert the action to a 'Goto' action as the payload is cannot be converted."
            )
            return action

        raw_output = action.raw_output

        if raw_output:
            deconstructed_action = SimBotDeconstructedAction.from_raw_action(raw_output)
            raw_output = f"goto <frame_token_{deconstructed_action.frame_index}> <vis_token_{deconstructed_action.object_index} {END_OF_TRAJECTORY_TOKEN}{PREDICTED_ACTION_DELIMITER}"

        return SimBotAction(
            id=0,
            type=SimBotActionType.Goto,
            raw_output=raw_output,
            payload=SimBotGotoPayload(object=cast(SimBotGotoObject, action.payload.object)),
        )

    def _get_previous_interaction_action(self, session: SimBotSession) -> SimBotAction:
        """Get the interaction action from the previous turn."""
        if not session.previous_valid_turn:
            raise AssertionError("There is no previous turn to get the action from.")

        if not session.previous_valid_turn.actions.interaction:
            raise AssertionError("There is no interaction action in the previous valid turn")

        return session.previous_valid_turn.actions.interaction
