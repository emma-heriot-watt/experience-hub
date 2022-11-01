import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event
from time import sleep
from typing import Any

from loguru import logger
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
    PlaceholderVisionClient,
    SimBotAuxiliaryMetadataClient,
    SimBotExtractedFeaturesClient,
    SimBotSessionDbClient,
)
from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.parsers.simbot import (
    SimBotActionPredictorOutputParser,
    SimBotLowASRConfidenceDetector,
    SimBotNLUOutputParser,
)
from emma_experience_hub.pipelines.simbot import (
    SimBotNLUPipeline,
    SimBotRequestProcessingPipeline,
    SimBotResponseGeneratorPipeline,
)


class SimBotControllerClients(BaseModel, arbitrary_types_allowed=True):
    """All the clients for the SimBot Controller API."""

    _exit = Event()

    feature_extractor: FeatureExtractorClient
    nlu_intent: EmmaPolicyClient
    action_predictor: EmmaPolicyClient
    session_db: SimBotSessionDbClient
    auxiliary_metadata_cache: SimBotAuxiliaryMetadataClient
    extracted_features_cache: SimBotExtractedFeaturesClient
    profanity_filter: ProfanityFilterClient
    utterance_generator: UtteranceGeneratorClient
    out_of_domain_detector: OutOfDomainDetectorClient
    button_detector: PlaceholderVisionClient

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
            auxiliary_metadata_cache=SimBotAuxiliaryMetadataClient(
                bucket_name=simbot_settings.simbot_cache_s3_bucket,
                local_cache_dir=simbot_settings.auxiliary_metadata_cache_dir,
            ),
            extracted_features_cache=SimBotExtractedFeaturesClient(
                bucket_name=simbot_settings.simbot_cache_s3_bucket,
                local_cache_dir=simbot_settings.extracted_features_cache_dir,
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
            button_detector=PlaceholderVisionClient(
                server_endpoint=simbot_settings.button_detector_url
            ),
        )

    def healthcheck(self, attempts: int = 1, interval: int = 0) -> bool:
        """Perform healthcheck, with retry intervals.

        To disable retries, just set the number of attempts to 1.
        """
        self._prepare_exit_signal()

        healthcheck_flag = False

        for attempt in range(attempts):
            healthcheck_flag = self._healthcheck_all_clients()

            # If the healthcheck flag is all good, break from the loop
            if healthcheck_flag or self._exit.is_set():
                break

            # Otherwise, report a failed attempt
            logger.error(f"Healthcheck attempt {attempt}/{attempts} failed.")

            # If attempt is not the last one, sleep for interval and go again
            if attempt < attempts - 1:
                logger.debug(f"Waiting for {interval} seconds and then trying again.")
                sleep(interval)

        return healthcheck_flag

    def _prepare_exit_signal(self) -> None:
        """Prepare the exit signal to handle KeyboardInterrupt events."""
        for sig in ("TERM", "HUP", "INT"):
            signal.signal(getattr(signal, f"SIG{sig}"), self._break_from_sleep)

    def _break_from_sleep(self, signum: int, _frame: Any) -> None:
        """Break from the sleep."""
        logger.info("Interrupted. Shutting down...")
        self._exit.set()

    def _healthcheck_all_clients(self) -> bool:
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
                except Exception:
                    logger.error("Failed to verify the healthcheck")
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
                asr_confidence_filter=SimBotLowASRConfidenceDetector(
                    avg_confidence_threshold=simbot_settings.asr_avg_confidence_threshold
                ),
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
                ),
                utterance_generator_client=clients.utterance_generator,
                button_detector_client=clients.button_detector,
            ),
        )


class SimBotControllerState(BaseModel, arbitrary_types_allowed=True):
    """State for the application."""

    settings: SimBotSettings
    clients: SimBotControllerClients
    pipelines: SimBotControllerPipelines

    def healthcheck(self, attempts: int = 1, interval: int = 0) -> bool:
        """Check the healthy of all the connected services."""
        return self.clients.healthcheck(attempts, interval)
