from typing import Optional

from loguru import logger

from emma_experience_hub.api.clients.simbot import SimBotUtteranceGeneratorClient
from emma_experience_hub.datamodels.simbot import (
    SimBotAction,
    SimBotActionType,
    SimBotDialogAction,
    SimBotIntent,
    SimBotIntentType,
    SimBotSession,
)
from emma_experience_hub.datamodels.simbot.payloads import SimBotDialogPayload


class SimBotAgentLanguageGenerationPipeline:
    """Generate language for the agent to say to the user."""

    def __init__(self, utterance_generator_client: SimBotUtteranceGeneratorClient) -> None:
        self._utterance_generator_client = utterance_generator_client

    def run(self, session: SimBotSession) -> Optional[SimBotDialogAction]:
        """Generate an utterance to send back to the user, if required."""
        if not session.current_turn.intent.agent:
            raise AssertionError("The agent should have an intent before calling this module.")

        action: Optional[SimBotDialogAction] = None

        # Generate dialog actions where the agent did not generate an interaction action
        if not action:
            action = self.handle_non_actionable_intents(session)

        if not action:
            action = self.handle_search_predictions(session)

        # If we wanted to generate an action and we failed to do so
        if not action:
            action = self.handle_failed_action_prediction(session)

        # If we successfully predicted an interaction action
        if not action:
            action = self.handle_successful_action_prediction(session)

        return action

    def handle_non_actionable_intents(
        self, session: SimBotSession
    ) -> Optional[SimBotDialogAction]:
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
        return self._generate_from_intent(
            session.current_turn.intent.agent, use_lightweight_dialog=False
        )

    def handle_failed_action_prediction(
        self, session: SimBotSession
    ) -> Optional[SimBotDialogAction]:
        """Handle dialog generation if a valid action was not generated."""
        agent_not_failed_action_prediction = (
            session.current_turn.intent.should_generate_interaction_action
            and session.current_turn.actions.interaction is not None
        )
        if agent_not_failed_action_prediction:
            return None

        intent = SimBotIntent(type=SimBotIntentType.generic_failure)
        return self._generate_from_intent(intent, use_lightweight_dialog=False)

    def handle_search_predictions(  # noqa: WPS212
        self, session: SimBotSession
    ) -> Optional[SimBotDialogAction]:
        """Handle search-related dialog generations."""
        # Agent intent should not be None
        if not session.current_turn.intent.agent:
            logger.debug("[NLG SEARCH]: Agent does not have an intent? This should not happen")
            return None

        # This handler is only for when we are trying to do a search routine
        if session.current_turn.intent.agent.type != SimBotIntentType.act_search:
            logger.debug("[NLG SEARCH]: Agent intent is not search, returning.")
            return None

        # Get the interaction action
        logger.debug("[NLG SEARCH]: Try get the interaction action from the agent")
        action = session.current_turn.actions.interaction

        # If there is no action, we did not find an object
        if not action:
            logger.debug(
                "[NLG SEARCH]: There is no interaction action, so we did not find an object and there is no planning steps left"
            )
            return self._generate_from_intent(
                SimBotIntent(type=SimBotIntentType.search_not_found_object),
                use_lightweight_dialog=False,
            )

        # If we are returning a Highlight action, it means we found the object.
        if action.type == SimBotActionType.Highlight:
            logger.debug("[NLG SEARCH]: We have found an object")
            return self._generate_from_intent(
                SimBotIntent(type=SimBotIntentType.search_found_object),
                use_lightweight_dialog=True,
            )

        # If we are returning a look around, return a lightweight dialog action
        if action.type == SimBotActionType.Look:
            logger.debug("[NLG SEARCH]: We are looking around for the object")
            return self._generate_from_intent(
                SimBotIntent(
                    type=SimBotIntentType.search_look_around,
                    action=SimBotActionType.LookAround,
                ),
                use_lightweight_dialog=True,
            )

        if action.type == SimBotActionType.GotoViewpoint:
            # If we are going to a viewpoint to look more
            logger.debug("[NLG SEARCH]: We are going to a new viewpoint")
            return self._generate_from_intent(
                SimBotIntent(
                    type=SimBotIntentType.search_goto_viewpoint,
                    action=SimBotActionType.GotoViewpoint,
                ),
                use_lightweight_dialog=True,
            )

        if action.type == SimBotActionType.GotoRoom:
            # If we are going to a room to look more
            logger.debug("[NLG SEARCH]: We are going to a new room")
            return self._generate_from_intent(
                SimBotIntent(
                    type=SimBotIntentType.search_goto_room,
                    action=SimBotActionType.GotoRoom,
                ),
                use_lightweight_dialog=True,
            )

        # We are going to the object indicated by the find routine
        if action.type == SimBotActionType.GotoObject:
            logger.debug("[NLG SEARCH]: We are going to the found object")
            return self._generate_from_intent(
                SimBotIntent(
                    type=SimBotIntentType.goto_object_success,
                    action=SimBotActionType.Goto,
                ),
                use_lightweight_dialog=False,
            )

        # If none of the above conditions fit, return None
        logger.debug("[NLG SEARCH]: None of the search conditions fit, returning `None`.")
        return None

    def handle_successful_action_prediction(
        self, session: SimBotSession
    ) -> Optional[SimBotDialogAction]:
        """Handle dialog generation for a successful action prediction."""
        interaction_action = session.current_turn.actions.interaction

        if not interaction_action:
            raise AssertionError("There should be an interaction action here.")

        # Check for end of trajectory token
        if not interaction_action.is_end_of_trajectory:
            return None

        # We should use the lightweight dialog if the utterance queue is not empty, since we are
        # going to act after this
        is_utterance_queue_not_empty = bool(session.current_state.utterance_queue)

        if interaction_action.is_goto_room:
            return self.handle_goto_room_action(
                interaction_action, use_lightweight_dialog=is_utterance_queue_not_empty
            )

        if interaction_action.is_goto_object:
            return self.handle_goto_object_action(
                interaction_action, use_lightweight_dialog=is_utterance_queue_not_empty
            )

        if interaction_action.is_low_level_navigation:
            return self.handle_low_level_navigation_action(
                interaction_action, use_lightweight_dialog=is_utterance_queue_not_empty
            )

        if interaction_action.is_object_interaction:
            return self.handle_object_interaction_action(
                interaction_action, use_lightweight_dialog=is_utterance_queue_not_empty
            )

        raise AssertionError("All predicted action types should have been handled?")

    def handle_goto_room_action(
        self, interaction_action: SimBotAction, use_lightweight_dialog: bool = False
    ) -> Optional[SimBotDialogAction]:
        """Generate dialog for goto room actions."""
        intent = SimBotIntent(
            type=SimBotIntentType.goto_room_success,
            entity=interaction_action.payload.entity_name,
            action=interaction_action.type,
        )
        return self._generate_from_intent(intent, use_lightweight_dialog)

    def handle_goto_object_action(
        self, interaction_action: SimBotAction, use_lightweight_dialog: bool = False
    ) -> Optional[SimBotDialogAction]:
        """Generate dialog for goto object actions."""
        intent = SimBotIntent(
            type=SimBotIntentType.goto_object_success,
            entity=interaction_action.payload.entity_name,
            action=interaction_action.type,
        )
        return self._generate_from_intent(intent, use_lightweight_dialog)

    def handle_low_level_navigation_action(
        self, interaction_action: SimBotAction, use_lightweight_dialog: bool = False
    ) -> Optional[SimBotDialogAction]:
        """Generate dialog for low-level navigation actions."""
        intent = SimBotIntent(
            type=SimBotIntentType.low_level_navigation_success,
            action=interaction_action.type,
        )
        return self._generate_from_intent(intent, use_lightweight_dialog)

    def handle_object_interaction_action(
        self, interaction_action: SimBotAction, use_lightweight_dialog: bool = False
    ) -> Optional[SimBotDialogAction]:
        """Generate dialog for object interaction actions."""
        intent = SimBotIntent(
            type=SimBotIntentType.low_level_navigation_success,
            entity=interaction_action.payload.entity_name,
            action=interaction_action.type,
        )
        return self._generate_from_intent(intent, use_lightweight_dialog)

    def _generate_from_intent(
        self, intent: SimBotIntent, use_lightweight_dialog: bool
    ) -> SimBotDialogAction:
        """Generate the utterance from the intent and return the dialog action."""
        utterance = self._utterance_generator_client.generate_from_intent(intent)
        return SimBotDialogAction(
            id=0,
            raw_output=utterance,
            type=SimBotActionType.LightweightDialog
            if use_lightweight_dialog
            else SimBotActionType.Dialog,
            payload=SimBotDialogPayload(value=utterance, intent=intent.type),
        )
