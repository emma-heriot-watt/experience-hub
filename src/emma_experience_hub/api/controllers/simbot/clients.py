import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event
from time import sleep
from typing import Any

from loguru import logger
from pydantic import BaseModel

from emma_experience_hub.api.clients import (
    Client,
    CompoundSplitterClient,
    ConfirmationResponseClassifierClient,
    FeatureExtractorClient,
    OutOfDomainDetectorClient,
    ProfanityFilterClient,
)
from emma_experience_hub.api.clients.simbot import (
    SimbotActionPredictionClient,
    SimBotAuxiliaryMetadataClient,
    SimBotExtractedFeaturesClient,
    SimBotFeaturesClient,
    SimBotHacksClient,
    SimBotNLUIntentClient,
    SimBotQAIntentClient,
    SimBotSessionDbClient,
)
from emma_experience_hub.common.settings import SimBotSettings


class SimBotControllerClients(BaseModel, arbitrary_types_allowed=True):
    """All the clients for the SimBot Controller API."""

    _exit = Event()

    features: SimBotFeaturesClient
    nlu_intent: SimBotNLUIntentClient
    action_predictor: SimbotActionPredictionClient
    session_db: SimBotSessionDbClient
    profanity_filter: ProfanityFilterClient
    out_of_domain_detector: OutOfDomainDetectorClient
    confirmation_response_classifier: ConfirmationResponseClassifierClient
    compound_splitter: CompoundSplitterClient
    simbot_hacks: SimBotHacksClient
    simbot_qa: SimBotQAIntentClient

    @classmethod
    def from_simbot_settings(cls, simbot_settings: SimBotSettings) -> "SimBotControllerClients":
        """Instantiate all the clients from the SimBot settings."""
        return cls(
            features=SimBotFeaturesClient(
                auxiliary_metadata_cache_client=SimBotAuxiliaryMetadataClient(
                    bucket_name=simbot_settings.simbot_cache_s3_bucket,
                    local_cache_dir=simbot_settings.auxiliary_metadata_cache_dir,
                ),
                feature_extractor_client=FeatureExtractorClient(
                    endpoint=simbot_settings.feature_extractor_url,
                    timeout=simbot_settings.client_timeout,
                ),
                features_cache_client=SimBotExtractedFeaturesClient(
                    bucket_name=simbot_settings.simbot_cache_s3_bucket,
                    local_cache_dir=simbot_settings.extracted_features_cache_dir,
                ),
            ),
            session_db=SimBotSessionDbClient(
                resource_region=simbot_settings.session_db_region,
                table_name=simbot_settings.session_db_memory_table_name,
            ),
            nlu_intent=SimBotNLUIntentClient(server_endpoint=simbot_settings.nlu_predictor_url),
            action_predictor=SimbotActionPredictionClient(
                server_endpoint=simbot_settings.action_predictor_url
            ),
            profanity_filter=ProfanityFilterClient(
                endpoint=simbot_settings.profanity_filter_url,
                timeout=simbot_settings.client_timeout,
            ),
            out_of_domain_detector=OutOfDomainDetectorClient(
                endpoint=simbot_settings.out_of_domain_detector_url,
                timeout=simbot_settings.client_timeout,
            ),
            confirmation_response_classifier=ConfirmationResponseClassifierClient(
                endpoint=simbot_settings.confirmation_classifier_url,
                timeout=simbot_settings.client_timeout,
            ),
            compound_splitter=CompoundSplitterClient(
                endpoint=simbot_settings.compound_splitter_url,
                timeout=simbot_settings.client_timeout,
            ),
            simbot_hacks=SimBotHacksClient(
                endpoint=simbot_settings.simbot_hacks_url,
                timeout=simbot_settings.client_timeout,
            ),
            simbot_qa=SimBotQAIntentClient(
                endpoint=simbot_settings.simbot_qa_url,
                timeout=simbot_settings.client_timeout,
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
            healthcheck_futures = {pool.submit(client.healthcheck): client for client in clients}

            for future in as_completed(healthcheck_futures):
                client = healthcheck_futures[future]
                try:
                    future.result()
                except Exception:
                    logger.error(f"Failed to verify the healthcheck for client `{client}`")
                    return False

        return True
