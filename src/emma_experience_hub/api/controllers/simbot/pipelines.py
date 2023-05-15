from pydantic import BaseModel

from emma_experience_hub.api.controllers.simbot.clients import SimBotControllerClients
from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.parsers.simbot import (
    SimBotActionPredictorOutputParser,
    SimBotLowASRConfidenceDetector,
    SimBotNLUOutputParser,
    SimBotPreviousActionParser,
    SimBotQAEntityParser,
    SimBotQAOutputParser,
    SimBotVisualGroundingOutputParser,
)
from emma_experience_hub.pipelines.simbot import (
    SimBotAgentActionGenerationPipeline,
    SimBotAgentIntentSelectionPipeline,
    SimBotAgentLanguageGenerationPipeline,
    SimbotAnticipatorPipeline,
    SimBotCompoundSplitterPipeline,
    SimBotEnvironmentErrorCatchingPipeline,
    SimBotEnvironmentIntentExtractionPipeline,
    SimBotFindObjectPipeline,
    SimBotRequestProcessingPipeline,
    SimBotUserIntentExtractionPipeline,
    SimBotUserUtteranceVerificationPipeline,
)


class SimBotControllerPipelines(BaseModel, arbitrary_types_allowed=True):
    """All the pipelines used by the SimBot Controller API."""

    request_processing: SimBotRequestProcessingPipeline
    user_utterance_verifier: SimBotUserUtteranceVerificationPipeline
    user_intent_extractor: SimBotUserIntentExtractionPipeline
    environment_intent_extractor: SimBotEnvironmentIntentExtractionPipeline
    agent_intent_selector: SimBotAgentIntentSelectionPipeline
    agent_action_generator: SimBotAgentActionGenerationPipeline
    agent_language_generator: SimBotAgentLanguageGenerationPipeline
    find_object: SimBotFindObjectPipeline
    compound_splitter: SimBotCompoundSplitterPipeline
    anticipator: SimbotAnticipatorPipeline

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
        compound_splitter = SimBotCompoundSplitterPipeline(
            clients.compound_splitter,
            _enable_compound_splitting=simbot_settings.feature_flags.enable_compound_splitting,
            _enable_coreference_resolution=simbot_settings.feature_flags.enable_coreference_resolution,
        )
        return cls(
            compound_splitter=compound_splitter,
            find_object=find_object,
            request_processing=SimBotRequestProcessingPipeline(
                session_db_client=clients.session_db,
            ),
            user_utterance_verifier=SimBotUserUtteranceVerificationPipeline(
                profanity_filter_client=clients.profanity_filter,
                low_asr_confidence_detector=SimBotLowASRConfidenceDetector(
                    avg_confidence_threshold=simbot_settings.asr_avg_confidence_threshold
                ),
                out_of_domain_detector_client=clients.out_of_domain_detector,
            ),
            user_intent_extractor=SimBotUserIntentExtractionPipeline(
                qa_intent_client=clients.simbot_qa,
                qa_intent_parser=SimBotQAOutputParser(
                    enable_incomplete_utterances_intent=simbot_settings.feature_flags.enable_incomplete_utterances_intent
                ),
                confirmation_response_classifier=clients.confirmation_response_classifier,
                _enable_object_related_questions=simbot_settings.feature_flags.enable_object_related_questions_from_user,
                _enable_simbot_qa=simbot_settings.feature_flags.enable_simbot_qa,
                _enable_confirmation_questions=simbot_settings.feature_flags.enable_confirmation_questions,
                _enable_clarification_questions=simbot_settings.feature_flags.enable_clarification_questions,
            ),
            environment_intent_extractor=SimBotEnvironmentIntentExtractionPipeline(),
            agent_intent_selector=SimBotAgentIntentSelectionPipeline(
                features_client=clients.features,
                simbot_qa_client=clients.simbot_qa,
                simbot_qa_entity_parser=SimBotQAEntityParser(),
                nlu_intent_client=clients.nlu_intent,
                nlu_intent_parser=SimBotNLUOutputParser(
                    intent_type_delimiter=simbot_settings.nlu_predictor_intent_type_delimiter
                ),
                environment_error_pipeline=SimBotEnvironmentErrorCatchingPipeline(),
                action_predictor_client=clients.action_predictor,
                compound_splitter_pipeline=compound_splitter,
                simbot_hacks_client=clients.simbot_hacks,
                _enable_clarification_questions=simbot_settings.feature_flags.enable_clarification_questions,
                _enable_confirmation_questions=simbot_settings.feature_flags.enable_confirmation_questions,
                _enable_search_actions=simbot_settings.feature_flags.enable_search_actions,
                _enable_search_after_no_match=simbot_settings.feature_flags.enable_search_after_no_match,
                _enable_search_after_missing_inventory=simbot_settings.feature_flags.enable_search_after_missing_inventory,
                _enable_high_level_planner=simbot_settings.feature_flags.enable_rasa_high_level_planner,
            ),
            agent_action_generator=SimBotAgentActionGenerationPipeline(
                features_client=clients.features,
                action_predictor_client=clients.action_predictor,
                action_predictor_response_parser=action_predictor_response_parser,
                previous_action_parser=SimBotPreviousActionParser(),
                find_object_pipeline=find_object,
                simbot_hacks_client=clients.simbot_hacks,
            ),
            agent_language_generator=SimBotAgentLanguageGenerationPipeline(
                prevent_default_response_as_lightweight=simbot_settings.feature_flags.prevent_default_response_as_lightweight
            ),
            anticipator=SimbotAnticipatorPipeline(
                simbot_hacks_client=clients.simbot_hacks,
                features_client=clients.features,
                _is_offline_evaluation=simbot_settings.feature_flags.enable_offline_evaluation,
            ),
        )
