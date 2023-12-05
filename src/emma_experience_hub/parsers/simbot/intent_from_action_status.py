from typing import Optional

from emma_experience_hub.datamodels.simbot import (
    SimBotEnvironmentIntentType,
    SimBotIntent,
    SimBotIntentType,
    SimBotSessionTurn,
)
from emma_experience_hub.parsers.parser import Parser


class SimBotIntentFromActionStatusParser(
    Parser[SimBotSessionTurn, Optional[SimBotIntent[SimBotEnvironmentIntentType]]]
):
    """Convert feedback from previous action status into intents for the agent."""

    __slots__ = ()

    def __call__(
        self, previous_turn: SimBotSessionTurn
    ) -> Optional[SimBotIntent[SimBotEnvironmentIntentType]]:
        """Process environment state changes to inform the agent of its standing in the world."""
        # If we received no action statuses, do nothing and return
        intent = self.convert_action_status_to_intent(previous_turn)

        if intent and not intent.type.is_environment_error:
            raise AssertionError(
                "Attempting to return an intent type that is not specifically allowed to be held by the environment."
            )

        return intent

    def convert_action_status_to_intent(
        self, previous_turn: SimBotSessionTurn
    ) -> Optional[SimBotIntent[SimBotEnvironmentIntentType]]:
        """Convert action statuses to an intent."""
        # If all previous actions were successful
        if previous_turn.actions.is_successful:
            return None

        return self._convert_error_action_to_intent(previous_turn)

    def _convert_error_action_to_intent(
        self, previous_turn: SimBotSessionTurn
    ) -> Optional[SimBotIntent[SimBotEnvironmentIntentType]]:
        """Convert the last action that caused an error into an intent."""
        erroneous_action = previous_turn.actions.interaction
        if not erroneous_action or not erroneous_action.status:
            return None

        # Try to convert the action status to one of the intents we handle
        try:
            intent_type = SimBotIntentType[erroneous_action.status.error_type.name]
        except KeyError:
            return None

        if not SimBotIntentType.is_environment_intent_type(intent_type):
            raise AssertionError("Intent type is not one of the environment intent types")

        return SimBotIntent[SimBotEnvironmentIntentType](
            type=intent_type,
            entity=erroneous_action.payload.entity_name,
            action=erroneous_action.type,
        )
