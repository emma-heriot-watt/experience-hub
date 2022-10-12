from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel

from emma_experience_hub.api.clients import (
    Client,
    EmmaPolicyClient,
    FeatureExtractorClient,
    OutOfDomainDetectorClient,
    ProfanityFilterClient,
    UtteranceGeneratorClient,
)
from emma_experience_hub.api.clients.simbot import (
    SimBotAuxiliaryMetadataS3Client,
    SimBotExtractedFeaturesFileSystemClient,
    SimBotSessionDbClient,
)
from emma_experience_hub.common.logging import get_logger
from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.parsers.simbot import (
    SimBotActionPredictorOutputParser,
    SimBotNLUOutputParser,
)
from emma_experience_hub.pipelines.simbot import (
    SimBotNLUPipeline,
    SimBotRequestProcessingPipeline,
    SimBotResponseGeneratorPipeline,
)


log = get_logger()


class SimBotControllerClients(BaseModel, arbitrary_types_allowed=True):
    """All the clients for the SimBot Controller API."""

    feature_extractor: FeatureExtractorClient
    nlu_intent: EmmaPolicyClient
    action_predictor: EmmaPolicyClient
    session_db: SimBotSessionDbClient
    auxiliary_metadata_cache: SimBotAuxiliaryMetadataS3Client
    extracted_features_cache: SimBotExtractedFeaturesFileSystemClient
    profanity_filter: ProfanityFilterClient
    utterance_generator: UtteranceGeneratorClient
    out_of_domain_detector: OutOfDomainDetectorClient

    @classmethod
    def from_simbot_settings(cls, simbot_settings: SimBotSettings) -> "SimBotControllerClients":
        """Instantiate all the clients from the SimBot settings."""
        return cls(
            feature_extractor=FeatureExtractorClient(
                server_endpoint=simbot_settings.feature_extractor_url
            ),
            session_db=SimBotSessionDbClient(
                resource_region=simbot_settings.session_db_region,
                table_name=simbot_settings.session_db_memory_table_name,
            ),
            auxiliary_metadata_cache=SimBotAuxiliaryMetadataS3Client(
                bucket_name=simbot_settings.auxiliary_metadata_s3_bucket,
                local_backup_root_path=simbot_settings.auxiliary_metadata_cache_dir,
            ),
            extracted_features_cache=SimBotExtractedFeaturesFileSystemClient(
                root_directory=simbot_settings.extracted_features_dir
            ),
            nlu_intent=EmmaPolicyClient(server_endpoint=simbot_settings.nlu_predictor_url),
            action_predictor=EmmaPolicyClient(
                server_endpoint=simbot_settings.action_predictor_url
            ),
            profanity_filter=ProfanityFilterClient(endpoint=simbot_settings.profanity_filter_url),
            utterance_generator=UtteranceGeneratorClient(
                endpoint=simbot_settings.utterance_generator_url
            ),
            out_of_domain_detector=OutOfDomainDetectorClient(
                endpoint=simbot_settings.out_of_domain_detector_url
            ),
        )

    def healthcheck(self) -> bool:
        """Check all the clients are healthy and running."""
        with ThreadPoolExecutor() as pool:
            clients: list[Client] = list(self.dict().values())
            # TODO: Should there be a timeout on the healthcheck for each client?
            #       If yes: how should timeouts be handled?
            #       If not: what if it hangs?
            healthcheck_futures = [pool.submit(client.healthcheck) for client in clients]

            for future in as_completed(healthcheck_futures):
                try:
                    future.result()
                except Exception as err:
                    log.exception("Failed to verify the healthcheck", exc_info=err)
                    return False

        return True


class SimBotControllerPipelines(BaseModel, arbitrary_types_allowed=True):
    """All the pipelines used by the SimBot Controller API."""

    request_processing: SimBotRequestProcessingPipeline
    nlu: SimBotNLUPipeline
    response_generation: SimBotResponseGeneratorPipeline

    @classmethod
    def from_controller_clients(
        cls, clients: SimBotControllerClients, simbot_settings: SimBotSettings
    ) -> "SimBotControllerPipelines":
        """Create the pipelines from the clients."""
        return cls(
            request_processing=SimBotRequestProcessingPipeline(
                feature_extractor_client=clients.feature_extractor,
                auxiliary_metadata_cache_client=clients.auxiliary_metadata_cache,
                extracted_features_cache_client=clients.extracted_features_cache,
                session_db_client=clients.session_db,
            ),
            nlu=SimBotNLUPipeline(
                extracted_features_cache_client=clients.extracted_features_cache,
                profanity_filter_client=clients.profanity_filter,
                out_of_domain_detector_client=clients.out_of_domain_detector,
                nlu_intent_client=clients.nlu_intent,
                nlu_intent_parser=SimBotNLUOutputParser(
                    intent_type_delimiter=simbot_settings.nlu_predictor_intent_type_delimiter
                ),
            ),
            response_generation=SimBotResponseGeneratorPipeline(
                extracted_features_cache_client=clients.extracted_features_cache,
                instruction_intent_client=clients.action_predictor,
                instruction_intent_response_parser=SimBotActionPredictorOutputParser(
                    action_delimiter=simbot_settings.action_predictor_delimiter,
                    eos_token=simbot_settings.action_predictor_eos_token,
                    utterance_generator_client=clients.utterance_generator,
                ),
                utterance_generator_client=clients.utterance_generator,
            ),
        )


class SimBotControllerState(BaseModel, arbitrary_types_allowed=True):
    """State for the application."""

    settings: SimBotSettings
    clients: SimBotControllerClients
    pipelines: SimBotControllerPipelines

    def healthcheck(self) -> bool:
        """Check the healthy of all the connected services."""
        return self.clients.healthcheck()
