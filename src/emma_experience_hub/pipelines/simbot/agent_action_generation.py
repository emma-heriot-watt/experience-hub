from typing import Callable, Optional

from loguru import logger

from emma_experience_hub.api.clients.simbot import (
    SimbotActionPredictionClient,
    SimBotFeaturesClient,
)
from emma_experience_hub.datamodels.simbot import (
    SimBotAction,
    SimBotIntent,
    SimBotIntentType,
    SimBotSession,
)
from emma_experience_hub.parsers.simbot import (
    SimBotActionPredictorOutputParser,
    SimBotPreviousActionParser,
)
from emma_experience_hub.pipelines.simbot.find_object import SimBotFindObjectPipeline


class SimBotAgentActionGenerationPipeline:
    """Generate an environment interaction for the agent to perform on the environment.

    This class does not handle choosing or generating dialog actions.
    """

    def __init__(
        self,
        features_client: SimBotFeaturesClient,
        action_predictor_client: SimbotActionPredictionClient,
        action_predictor_response_parser: SimBotActionPredictorOutputParser,
        previous_action_parser: SimBotPreviousActionParser,
        find_object_pipeline: SimBotFindObjectPipeline,
    ) -> None:
        self._features_client = features_client
        self._action_predictor_client = action_predictor_client
        self._action_predictor_response_parser = action_predictor_response_parser
        self._previous_action_parser = previous_action_parser

        self._find_object_pipeline = find_object_pipeline

    def run(self, session: SimBotSession) -> Optional[SimBotAction]:
        """Generate an action to perform on the environment."""
        if not session.current_turn.intent.agent:
            raise AssertionError("The agent should have an intent before calling this pipeline.")

        try:
            action_intent_handler = self._get_action_intent_handler(
                session.current_turn.intent.agent
            )
        except KeyError:
            logger.debug(
                f"Agent intent ({session.current_turn.intent.agent}) does not require the agent to generate an action that interacts with the environment."
            )
            return None

        try:
            return action_intent_handler(session)
        except Exception:
            logger.error("Failed to convert the agent intent to executable form.")
            return None

    def handle_act_intent(self, session: SimBotSession) -> Optional[SimBotAction]:
        """Generate an action when we want to just act."""
        try:
            return self._predict_action_from_template_matching(session)
        except Exception:
            return self._predict_action_from_emma_policy(session)

    def handle_act_previous_intent(self, session: SimBotSession) -> Optional[SimBotAction]:
        """Get the action from the previous turn."""
        # If there is a routine is in progress, continue it
        if session.is_find_object_in_progress:
            return self.handle_act_search_intent(session)

        return self._previous_action_parser(session)

    def handle_act_search_intent(self, session: SimBotSession) -> Optional[SimBotAction]:
        """Handle the search for object intent."""
        return self._find_object_pipeline.run(session)

    def _get_action_intent_handler(
        self, intent: SimBotIntent
    ) -> Callable[[SimBotSession], Optional[SimBotAction]]:
        """Get the handler to use when generating an action to perform on the environment."""
        switcher = {
            SimBotIntentType.act_low_level: self.handle_act_intent,
            SimBotIntentType.act_previous: self.handle_act_previous_intent,
            SimBotIntentType.act_search: self.handle_act_search_intent,
        }

        return switcher[intent.type]

    def _predict_action_from_template_matching(self, session: SimBotSession) -> SimBotAction:
        """Generate an action from the raw-text matching templater."""
        if not session.current_turn.utterances:
            raise AssertionError("No utterances to try match with")

        raw_text_match_prediction = (
            self._action_predictor_client.get_low_level_prediction_from_raw_text(
                dialogue_history=session.current_turn.utterances,
                environment_state_history=[],
            )
        )

        if raw_text_match_prediction is None:
            raise AssertionError("Cannot match raw text to template.")

        # Try to parse the outcome
        try:
            return self._action_predictor_response_parser(
                raw_text_match_prediction, extracted_features=[]
            )
        except Exception as err:
            logger.error(
                f"Cannot convert matched template ({raw_text_match_prediction}) to SimBotAction?"
            )
            raise err

    def _predict_action_from_emma_policy(self, session: SimBotSession) -> Optional[SimBotAction]:
        """Generate an action from the EMMA policy client."""
        turns_within_interaction_window = session.get_turns_within_interaction_window()
        environment_state_history = session.get_environment_state_history_from_turns(
            turns_within_interaction_window,
            self._features_client.get_features,
        )
        dialogue_history = session.get_dialogue_history_from_session_turns(
            turns_within_interaction_window
        )
        raw_action_prediction = self._action_predictor_client.generate(
            dialogue_history=dialogue_history, environment_state_history=environment_state_history
        )

        # Get the flattened list of extracted features from the state history
        extracted_features = [
            feats for turn in environment_state_history for feats in turn.features
        ]

        # Parse the response into an action
        try:
            return self._action_predictor_response_parser(
                raw_action_prediction,
                extracted_features=extracted_features,
                num_frames_in_current_turn=len(environment_state_history[-1].features),
            )
        except AssertionError:
            logger.error(f"Unable to parse a response for the output {raw_action_prediction}")
            return None
