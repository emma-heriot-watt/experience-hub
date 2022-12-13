from typing import Optional

from loguru import logger

from emma_experience_hub.api.clients.simbot import SimbotActionPredictionClient
from emma_experience_hub.datamodels.simbot import (
    SimBotAction,
    SimBotIntent,
    SimBotIntentType,
    SimBotSession,
)
from emma_experience_hub.parsers.simbot import SimBotActionPredictorOutputParser


class SimbotRawTextMatchActionPredictionPipeline:
    """Generate an environment interaction for the agent to perform on the environment.

    This class does not handle choosing or generating dialog actions.
    """

    def __init__(
        self,
        action_predictor_client: SimbotActionPredictionClient,
        action_predictor_response_parser: SimBotActionPredictorOutputParser,
    ) -> None:

        self._action_predictor_client = action_predictor_client
        self._action_predictor_response_parser = action_predictor_response_parser

    def run(self, session: SimBotSession) -> tuple[Optional[SimBotIntent], Optional[SimBotAction]]:
        """Run the raw text matching pipeline."""
        # If the user has said something, give that priority.
        if session.current_turn.intent.user:
            logger.debug(
                "Trying to match the user utterance to a low level action with raw text match."
            )
            return self._process_utterance_with_raw_text_match(session)

        # Let the following pipelines handle the rest of the cases.
        return None, None

    def _process_utterance_with_raw_text_match(
        self, session: SimBotSession
    ) -> tuple[Optional[SimBotIntent], Optional[SimBotAction]]:
        """Determine what the agent should do next from the user intent."""
        raw_text_match_prediction = (
            self._action_predictor_client.get_low_level_prediction_from_raw_text(
                dialogue_history=session.current_turn.utterances,
                environment_state_history=[],
            )
        )
        if raw_text_match_prediction is not None:
            decoded_action = self._action_predictor_response_parser(
                raw_text_match_prediction, extracted_features=[]
            )
            return SimBotIntent(type=SimBotIntentType.act_low_level), decoded_action
        return None, None
