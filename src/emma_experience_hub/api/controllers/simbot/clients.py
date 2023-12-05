import signal
from pathlib import Path
from threading import Event
from time import sleep
from typing import Any

from loguru import logger
from pydantic import BaseModel

from emma_experience_hub.api.clients import Client, FeatureExtractorClient
from emma_experience_hub.api.clients.simbot import (
    SimbotActionPredictionClient,
    SimBotAuxiliaryMetadataClient,
    SimBotCRIntentClient,
    SimBotExtractedFeaturesClient,
    SimBotFeaturesClient,
    SimBotPlaceholderVisionClient,
    SimBotSessionDbClient,
)
from emma_experience_hub.common.settings import SimBotSettings


class SimBotControllerClients(BaseModel, arbitrary_types_allowed=True):
    """All the clients for the SimBot Controller API."""

    _exit = Event()

    features: SimBotFeaturesClient
    cr_intent: SimBotCRIntentClient
    action_predictor: SimbotActionPredictionClient
    session_db: SimBotSessionDbClient

    @classmethod
    def from_simbot_settings(cls, simbot_settings: SimBotSettings) -> "SimBotControllerClients":
        """Instantiate all the clients from the SimBot settings."""
        return cls(
            features=SimBotFeaturesClient(
                auxiliary_metadata_cache_client=SimBotAuxiliaryMetadataClient(
                    local_cache_dir=simbot_settings.auxiliary_metadata_cache_dir,
                ),
                feature_extractor_client=FeatureExtractorClient(
                    endpoint=simbot_settings.feature_extractor_url,
                    timeout=simbot_settings.client_timeout,
                ),
                features_cache_client=SimBotExtractedFeaturesClient(
                    local_cache_dir=simbot_settings.extracted_features_cache_dir,
                ),
                placeholder_vision_client=SimBotPlaceholderVisionClient(
                    endpoint=simbot_settings.placeholder_vision_url,
                    timeout=simbot_settings.client_timeout,
                ),
            ),
            session_db=SimBotSessionDbClient(
                db_file=Path(simbot_settings.session_local_db_file),
            ),
            cr_intent=SimBotCRIntentClient(
                endpoint=simbot_settings.cr_predictor_url,
                timeout=simbot_settings.client_timeout,
            ),
            action_predictor=SimbotActionPredictionClient(
                endpoint=simbot_settings.action_predictor_url,
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
        clients: list[Client] = list(self.dict().values())
        for client in clients:
            if not client.healthcheck():
                logger.exception(f"Failed to verify the healthcheck for client `{client}`")
                return False

        return True
