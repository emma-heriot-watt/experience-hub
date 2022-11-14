from typing import Optional

from emma_experience_hub.api.clients.simbot import SimBotUtteranceGeneratorClient
from emma_experience_hub.datamodels.simbot import (
    SimBotAction,
    SimBotActionType,
    SimBotIntent,
    SimBotIntentType,
    SimBotSession,
)
from emma_experience_hub.datamodels.simbot.payloads import SimBotDialogPayload


class SimBotAgentLanguageGenerationPipeline:
    """Generate language for the agent to say to the user."""

    def __init__(self, utterance_generator_client: SimBotUtteranceGeneratorClient) -> None:
        self._utterance_generator_client = utterance_generator_client

    def run(self, session: SimBotSession) -> Optional[SimBotAction]:
        """Generate an utterance to send back to the user, if required."""
        if not session.current_turn.intent.agent:
            raise AssertionError("The agent should have an intent before calling this module.")

        action: Optional[SimBotAction] = None

        # Generate dialog actions where the agent did not generate an interaction action
        if not action:
            action = self.handle_non_actionable_intents(session)

        # If we wanted to generate an action and we failed to do so
        if not action:
            action = self.handle_failed_action_prediction(session)

        # If we successfully predicted an interaction action
        if not action:
            action = self.handle_successful_action_prediction(session)

        return action

    def handle_non_actionable_intents(self, session: SimBotSession) -> Optional[SimBotAction]:
        """Generate utterances for non-actionable intents.

        These are basically all cases where the agent does not want to generate an action.
        """
        # Agent intent should not be None
        if not session.current_turn.intent.agent:
            return None

        # If the agent intent should have generated an action, return None
        if session.current_turn.intent.should_generate_interaction_action:
            return None

        # Otherwise, provide that intent to the utterance generator
        return self._generate_from_intent(session.current_turn.intent.agent)

    def handle_failed_action_prediction(self, session: SimBotSession) -> Optional[SimBotAction]:
        """Handle dialog generation if a valid action was not generated."""
        agent_not_failed_action_prediction = (
            session.current_turn.intent.should_generate_interaction_action
            and session.current_turn.actions.interaction is None
        )
        if agent_not_failed_action_prediction:
            return None

        intent = SimBotIntent(type=SimBotIntentType.generic_failure)
        return self._generate_from_intent(intent)

    def handle_successful_action_prediction(
        self, session: SimBotSession
    ) -> Optional[SimBotAction]:
        """Handle dialog generation for a successful action prediction."""
        interaction_action = session.current_turn.actions.interaction

        if not interaction_action:
            raise AssertionError("There should be an interaction action here.")

        # Check for end of trajectory token
        if not interaction_action.is_end_of_trajectory:
            return None

        if interaction_action.is_goto_room:
            return self.handle_goto_room_action(interaction_action)

        if interaction_action.is_goto_object:
            return self.handle_goto_object_action(interaction_action)

        if interaction_action.is_low_level_navigation:
            return self.handle_low_level_navigation_action(interaction_action)

        if interaction_action.is_object_interaction:
            return self.handle_object_interaction_action(interaction_action)

        raise AssertionError("All predicted action types should have been handled?")

    def handle_goto_room_action(self, interaction_action: SimBotAction) -> Optional[SimBotAction]:
        """Generate dialog for goto room actions."""
        intent = SimBotIntent(
            type=SimBotIntentType.goto_room_success,
            entity=interaction_action.payload.entity_name,
            action=interaction_action.type.value,
        )
        return self._generate_from_intent(intent)

    def handle_goto_object_action(
        self, interaction_action: SimBotAction
    ) -> Optional[SimBotAction]:
        """Generate dialog for goto object actions."""
        intent = SimBotIntent(
            type=SimBotIntentType.goto_object_success,
            entity=interaction_action.payload.entity_name,
            action=interaction_action.type.value,
        )
        return self._generate_from_intent(intent)

    def handle_low_level_navigation_action(
        self, interaction_action: SimBotAction
    ) -> Optional[SimBotAction]:
        """Generate dialog for low-level navigation actions."""
        intent = SimBotIntent(
            type=SimBotIntentType.low_level_navigation_success,
            action=interaction_action.type.value,
        )
        return self._generate_from_intent(intent)

    def handle_object_interaction_action(
        self, interaction_action: SimBotAction
    ) -> Optional[SimBotAction]:
        """Generate dialog for object interaction actions."""
        intent = SimBotIntent(
            type=SimBotIntentType.low_level_navigation_success,
            entity=interaction_action.payload.entity_name,
            action=interaction_action.type.value,
        )
        return self._generate_from_intent(intent)

    def _generate_from_intent(self, intent: SimBotIntent) -> SimBotAction:
        """Generate the utterance from the intent and return the dialog action."""
        utterance = self._utterance_generator_client.generate_from_intent(intent)
        return SimBotAction(
            id=0,
            raw_output=utterance,
            type=SimBotActionType.Dialog,
            payload=SimBotDialogPayload(value=utterance, intent=intent.type),
        )
