from typing import Callable, Optional

from loguru import logger

from emma_experience_hub.api.clients.simbot import (
    SimbotActionPredictionClient,
    SimBotFeaturesClient,
    SimBotHacksClient,
    SimBotNLUIntentClient,
    SimBotQAIntentClient,
)
from emma_experience_hub.datamodels.simbot import (
    SimBotAgentIntents,
    SimBotAnyUserIntentType,
    SimBotIntent,
    SimBotIntentType,
    SimBotNLUIntentType,
    SimBotSession,
    SimBotUserIntentType,
)
from emma_experience_hub.functions.simbot.agent_intent_selection import (
    SimBotActHandler,
    SimBotClarificationHandler,
    SimBotConfirmationHandler,
    SimBotObjectQAHandler,
    set_find_object_in_progress_intent,
)
from emma_experience_hub.parsers import NeuralParser
from emma_experience_hub.parsers.simbot import SimBotQAEntityParser
from emma_experience_hub.pipelines.simbot.compound_splitter import SimBotCompoundSplitterPipeline
from emma_experience_hub.pipelines.simbot.environment_error_catching import (
    SimBotEnvironmentErrorCatchingPipeline,
)


class SimBotAgentIntentSelectionPipeline:
    """Determine HOW the agent should act given all the information.

    By only caring about how the agent should act, we separate intent extraction from the users
    expectations and how the agent chooses to act to those expectations.
    """

    def __init__(
        self,
        features_client: SimBotFeaturesClient,
        simbot_qa_client: SimBotQAIntentClient,
        simbot_qa_entity_parser: SimBotQAEntityParser,
        nlu_intent_client: SimBotNLUIntentClient,
        nlu_intent_parser: NeuralParser[SimBotIntent[SimBotNLUIntentType]],
        action_predictor_client: SimbotActionPredictionClient,
        environment_error_pipeline: SimBotEnvironmentErrorCatchingPipeline,
        compound_splitter_pipeline: SimBotCompoundSplitterPipeline,
        simbot_hacks_client: SimBotHacksClient,
        _enable_clarification_questions: bool = True,
        _enable_confirmation_questions: bool = True,
        _enable_search_actions: bool = True,
        _enable_search_after_no_match: bool = True,
        _enable_search_after_missing_inventory: bool = True,
        _enable_high_level_planner: bool = True,
        _enable_simbot_raw_text_match: bool = True,
    ) -> None:
        self.clarification_handler = SimBotClarificationHandler()
        self._features_client = features_client
        self.simbot_object_qa_handler = SimBotObjectQAHandler(
            simbot_qa_client=simbot_qa_client,
            simbot_qa_entity_parser=simbot_qa_entity_parser,
            _enable_confirmation_questions=_enable_confirmation_questions,
        )
        self.confirmation_handler = SimBotConfirmationHandler(_enable_search_after_no_match)
        self.act_handler = SimBotActHandler(
            features_client=features_client,
            nlu_intent_client=nlu_intent_client,
            nlu_intent_parser=nlu_intent_parser,
            action_predictor_client=action_predictor_client,
            compound_splitter_pipeline=compound_splitter_pipeline,
            simbot_hacks_client=simbot_hacks_client,
            _enable_clarification_questions=_enable_clarification_questions,
            _enable_confirmation_questions=_enable_confirmation_questions,
            _enable_search_actions=_enable_search_actions,
            _enable_search_after_no_match=_enable_search_after_no_match,
            _enable_search_after_missing_inventory=_enable_search_after_missing_inventory,
            _enable_high_level_planner=_enable_high_level_planner,
            _enable_simbot_raw_text_match=_enable_simbot_raw_text_match,
        )
        self._environment_error_pipeline = environment_error_pipeline

    def run(self, session: SimBotSession) -> SimBotAgentIntents:  # noqa: WPS212
        """Decide next action for the agent."""
        # If there was an environment error, try to catch it and continue acting - else respond to it.
        intents = self._set_intent_from_environment(session)
        if intents is not None:
            return intents

        # If the user has said something, determine the agent intent
        if session.current_turn.intent.user:
            logger.debug("Getting agent intent from user intent.")

            # check for object-qa and return
            if session.current_turn.intent.user.is_user_qa_about_object:
                return self.handle_object_qa_intent(session)

            # If we have received an invalid utterance, the agent does not act
            should_skip_action_selection = self._should_skip_action_selection(
                session.current_turn.intent.user
            )
            if should_skip_action_selection:
                return SimBotAgentIntents()

            # Otherwise, extract the intent from the user utterance
            if SimBotIntentType.is_user_intent_type(session.current_turn.intent.user):
                return self.extract_intent_from_user_utterance(
                    session.current_turn.intent.user, session
                )

        # If we are currently in the middle of a search routine, continue it.
        if session.is_find_object_in_progress:
            logger.debug("Setting agent intent to search since we are currently in progress")
            return set_find_object_in_progress_intent(session)

        # If the previous action had a stop token and we used a lightweight dialog action, we need
        # to skip the action generator
        if self._used_lightweight_dialog_with_stop_token(session):
            return SimBotAgentIntents(
                verbal_interaction=SimBotIntent(type=SimBotIntentType.generic_success)
            )

        return SimBotAgentIntents(
            physical_interaction=SimBotIntent(type=SimBotIntentType.act_one_match)
        )

    def extract_intent_from_user_utterance(
        self, user_intent: SimBotUserIntentType, session: SimBotSession
    ) -> SimBotAgentIntents:
        """Determine what the agent should do next from the user intent.

        The `UserIntentExtractorPipeline` will determine whether or not the user has said something
        that we cannot/should not act on. Therefore, we can use this function to determine the
        action given the other cases, and return if none of those cases fit.
        """
        try:
            user_intent_handler = self._get_user_intent_handler(user_intent)
            agent_intents = user_intent_handler(session)
        except Exception:
            logger.exception("Could not extract agent intent.")
            agent_intents = None

        if agent_intents is not None:
            return agent_intents
        # In all other cases, just return the intent as the agent _should_ know how to act.
        return SimBotAgentIntents(
            physical_interaction=SimBotIntent(type=SimBotIntentType.act_one_match)
        )

    def handle_act_intent(self, session: SimBotSession) -> Optional[SimBotAgentIntents]:
        """Select the action intent when the user wants us to act."""
        return self.act_handler.run(session)

    def handle_clarification_intent(self, session: SimBotSession) -> Optional[SimBotAgentIntents]:
        """Select the action intent when the user intent is responding to a clarification."""
        return self.clarification_handler.run(session)

    def handle_confimation_intent(self, session: SimBotSession) -> Optional[SimBotAgentIntents]:
        """Select the action intent when the user intent is responding to a confirmation."""
        intents = self.confirmation_handler.run(session)
        # If the confirmation handler did not set the intent, use the act handler
        if intents is None:
            return self.handle_act_intent(session)
        return intents

    def handle_object_qa_intent(self, session: SimBotSession) -> Optional[SimBotAgentIntents]:
        """Get the entities when the user_qa is related to objects."""
        intents = self.simbot_object_qa_handler.run(session)
        return intents

    def _get_user_intent_handler(
        self, user_intent: SimBotUserIntentType
    ) -> Callable[[SimBotSession], Optional[SimBotAgentIntents]]:
        """Get the handler to use when selecting the agent intent."""
        switcher = {
            SimBotIntentType.act: self.handle_act_intent,
            SimBotIntentType.clarify_answer: self.handle_clarification_intent,
            SimBotIntentType.confirm_yes: self.handle_confimation_intent,
            SimBotIntentType.confirm_no: self.handle_confimation_intent,
        }
        return switcher[user_intent]

    def _used_lightweight_dialog_with_stop_token(self, session: SimBotSession) -> bool:
        """Return True if we returned a lightweight dialog with the end of trajectory.

        While it appears that the action generation model can handle this automatically, the time
        it takes to extract the features for the action generation is taking too long. Therefore we
        need to step-in and bypass that entire process.
        """
        if not session.previous_valid_turn:
            return False

        previous_dialog_was_lightweight = (
            session.previous_valid_turn.actions.dialog is not None
            and session.previous_valid_turn.actions.dialog.is_lightweight_dialog
        )
        previous_action_was_end_of_trajectory = (
            session.previous_valid_turn.actions.interaction is not None
            and session.previous_valid_turn.actions.interaction.is_end_of_trajectory
        )

        return previous_action_was_end_of_trajectory and previous_dialog_was_lightweight

    def _should_skip_action_selection(self, user_intent_type: SimBotAnyUserIntentType) -> bool:
        """No action needed after an invalid utterance, QA or an environment error."""
        return user_intent_type.is_invalid_user_utterance or user_intent_type.is_user_qa

    def _set_intent_from_environment(self, session: SimBotSession) -> Optional[SimBotAgentIntents]:
        if session.current_turn.intent.environment is None:
            return None
        # Can we handle the environment error? If not, return empty agent intents
        if not self._environment_error_pipeline(session):
            logger.debug("Returning None as environment errors do not cause the agent to act.")
            session.current_state.utterance_queue.reset()
            session.current_state.find_queue.reset()
            return SimBotAgentIntents()
        # If it is an unsupported navigation that we can handle, we need to confirm before acting
        if self._environment_error_pipeline.is_handling_unsupported_navigation(session):
            return SimBotAgentIntents(
                verbal_interaction=SimBotIntent(type=SimBotIntentType.confirm_before_plan)
            )
        return None
