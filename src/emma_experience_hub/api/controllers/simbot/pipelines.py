from pydantic import BaseModel

from emma_experience_hub.api.controllers.simbot.clients import SimBotControllerClients
from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.parsers.simbot import (
    SimBotActionPredictorOutputParser,
    SimBotCROutputParser,
    SimBotPreviousActionParser,
    SimBotVisualGroundingOutputParser,
)
from emma_experience_hub.pipelines.simbot import (
    SimBotAgentActionGenerationPipeline,
    SimBotAgentIntentSelectionPipeline,
    SimBotEnvironmentErrorCatchingPipeline,
    SimBotEnvironmentIntentExtractionPipeline,
    SimBotFindObjectPipeline,
    SimBotRequestProcessingPipeline,
    SimBotUserIntentExtractionPipeline,
)


class SimBotControllerPipelines(BaseModel, arbitrary_types_allowed=True):
    """All the pipelines used by the SimBot Controller API."""

    request_processing: SimBotRequestProcessingPipeline
    user_intent_extractor: SimBotUserIntentExtractionPipeline
    environment_intent_extractor: SimBotEnvironmentIntentExtractionPipeline
    agent_intent_selector: SimBotAgentIntentSelectionPipeline
    agent_action_generator: SimBotAgentActionGenerationPipeline
    find_object: SimBotFindObjectPipeline

    @classmethod
    def from_clients(
        cls, clients: SimBotControllerClients, simbot_settings: SimBotSettings
    ) -> "SimBotControllerPipelines":
        """Create the pipelines from the clients."""
        find_object = SimBotFindObjectPipeline.from_planner_type(
            features_client=clients.features,
            action_predictor_client=clients.action_predictor,
            planner_type=simbot_settings.feature_flags.search_planner_type,
            visual_grounding_output_parser=SimBotVisualGroundingOutputParser(),
            enable_grab_from_history=simbot_settings.feature_flags.enable_grab_from_history,
            gfh_location_type=simbot_settings.feature_flags.gfh_location_type,
            _enable_scanning_found_object=simbot_settings.feature_flags.enable_scanning_during_search,
            scan_area_threshold=simbot_settings.feature_arguments.scan_area_threshold,
        )
        action_predictor_response_parser = SimBotActionPredictorOutputParser()
        return cls(
            find_object=find_object,
            request_processing=SimBotRequestProcessingPipeline(
                session_db_client=clients.session_db,
            ),
            user_intent_extractor=SimBotUserIntentExtractionPipeline(),
            environment_intent_extractor=SimBotEnvironmentIntentExtractionPipeline(),
            agent_intent_selector=SimBotAgentIntentSelectionPipeline(
                features_client=clients.features,
                cr_intent_client=clients.cr_intent,
                cr_intent_parser=SimBotCROutputParser(
                    intent_type_delimiter=simbot_settings.cr_predictor_intent_type_delimiter
                ),
                environment_error_pipeline=SimBotEnvironmentErrorCatchingPipeline(),
                action_predictor_client=clients.action_predictor,
                _enable_clarification_questions=simbot_settings.feature_flags.enable_clarification_questions,
                _enable_search_actions=simbot_settings.feature_flags.enable_search_actions,
                _enable_search_after_no_match=simbot_settings.feature_flags.enable_search_after_no_match,
                _enable_search_after_missing_inventory=simbot_settings.feature_flags.enable_search_after_missing_inventory,
            ),
            agent_action_generator=SimBotAgentActionGenerationPipeline(
                features_client=clients.features,
                action_predictor_client=clients.action_predictor,
                action_predictor_response_parser=action_predictor_response_parser,
                previous_action_parser=SimBotPreviousActionParser(),
                find_object_pipeline=find_object,
            ),
        )
