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
)
from emma_experience_hub.api.clients.simbot import (
    PlaceholderVisionClient,
    SimBotAuxiliaryMetadataClient,
    SimBotExtractedFeaturesClient,
    SimBotFeaturesClient,
    SimBotSessionDbClient,
    SimBotUtteranceGeneratorClient,
)
from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.datamodels.simbot import SimBotRequest, SimBotResponse, SimBotSession
from emma_experience_hub.parsers.simbot import (
    SimBotActionPredictorOutputParser,
    SimBotLowASRConfidenceDetector,
    SimBotNLUOutputParser,
)
from emma_experience_hub.pipelines.simbot import (
    SimBotAgentActionGenerationPipeline,
    SimBotAgentIntentSelectionPipeline,
    SimBotAgentLanguageGenerationPipeline,
    SimBotEnvironmentIntentExtractionPipeline,
    SimBotRequestProcessingPipeline,
    SimBotUserIntentExtractionPipeline,
    SimBotUserUtteranceVerificationPipeline,
)


class SimBotControllerClients(BaseModel, arbitrary_types_allowed=True):
    """All the clients for the SimBot Controller API."""

    _exit = Event()

    features: SimBotFeaturesClient
    nlu_intent: EmmaPolicyClient
    action_predictor: EmmaPolicyClient
    session_db: SimBotSessionDbClient
    profanity_filter: ProfanityFilterClient
    utterance_generator: SimBotUtteranceGeneratorClient
    out_of_domain_detector: OutOfDomainDetectorClient
    button_detector: PlaceholderVisionClient

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
                    endpoint=simbot_settings.feature_extractor_url
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
            nlu_intent=EmmaPolicyClient(server_endpoint=simbot_settings.nlu_predictor_url),
            action_predictor=EmmaPolicyClient(
                server_endpoint=simbot_settings.action_predictor_url
            ),
            profanity_filter=ProfanityFilterClient(endpoint=simbot_settings.profanity_filter_url),
            utterance_generator=SimBotUtteranceGeneratorClient(
                endpoint=simbot_settings.utterance_generator_url
            ),
            out_of_domain_detector=OutOfDomainDetectorClient(
                endpoint=simbot_settings.out_of_domain_detector_url
            ),
            button_detector=PlaceholderVisionClient(endpoint=simbot_settings.button_detector_url),
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
    user_utterance_verifier: SimBotUserUtteranceVerificationPipeline
    user_intent_extractor: SimBotUserIntentExtractionPipeline
    environment_intent_extractor: SimBotEnvironmentIntentExtractionPipeline
    agent_intent_selector: SimBotAgentIntentSelectionPipeline
    agent_action_generator: SimBotAgentActionGenerationPipeline
    agent_language_generator: SimBotAgentLanguageGenerationPipeline

    @classmethod
    def from_clients(
        cls, clients: SimBotControllerClients, simbot_settings: SimBotSettings
    ) -> "SimBotControllerPipelines":
        """Create the pipelines from the clients."""
        return cls(
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
                _disable_clarification_questions=simbot_settings.disable_clarification_questions,
                _disable_clarification_confirmation=simbot_settings.disable_clarification_confirmation,
            ),
            environment_intent_extractor=SimBotEnvironmentIntentExtractionPipeline(),
            agent_intent_selector=SimBotAgentIntentSelectionPipeline(
                features_client=clients.features,
                nlu_intent_client=clients.nlu_intent,
                nlu_intent_parser=SimBotNLUOutputParser(
                    intent_type_delimiter=simbot_settings.nlu_predictor_intent_type_delimiter
                ),
                _disable_clarification_questions=simbot_settings.disable_clarification_questions,
            ),
            agent_action_generator=SimBotAgentActionGenerationPipeline(
                features_client=clients.features,
                button_detector_client=clients.button_detector,
                action_predictor_client=clients.action_predictor,
                action_predictor_response_parser=SimBotActionPredictorOutputParser(
                    action_delimiter=simbot_settings.action_predictor_delimiter,
                    eos_token=simbot_settings.action_predictor_eos_token,
                ),
            ),
            agent_language_generator=SimBotAgentLanguageGenerationPipeline(
                utterance_generator_client=clients.utterance_generator,
            ),
        )


class SimBotController:
    """Inference pipeline for the live SimBot Challenge."""

    def __init__(
        self,
        settings: SimBotSettings,
        clients: SimBotControllerClients,
        pipelines: SimBotControllerPipelines,
    ) -> None:
        self.settings = settings
        self.clients = clients
        self.pipelines = pipelines

    @classmethod
    def from_simbot_settings(cls, simbot_settings: SimBotSettings) -> "SimBotController":
        """Instantiate the controller from the settings."""
        clients = SimBotControllerClients.from_simbot_settings(simbot_settings)
        pipelines = SimBotControllerPipelines.from_clients(clients, simbot_settings)

        return cls(settings=simbot_settings, clients=clients, pipelines=pipelines)

    def healthcheck(self, attempts: int = 1, interval: int = 0) -> bool:
        """Check the healthy of all the connected services."""
        return self.clients.healthcheck(attempts, interval)

    def handle_request_from_simbot_arena(self, request: SimBotRequest) -> SimBotResponse:
        """Handle an incoming request from the SimBot arena."""
        session = self.load_session_from_request(request)
        session = self.extract_intent_from_user_utterance(session)
        session = self.extract_intent_from_environment_feedback(session)
        session = self.decide_what_the_agent_should_do(session)
        session = self.generate_interaction_action_if_needed(session)
        session = self.generate_language_action_if_needed(session)

        self._upload_session_turn_to_database(session)

        return session.current_turn.convert_to_simbot_response()

    def load_session_from_request(self, simbot_request: SimBotRequest) -> SimBotSession:
        """Load the entire session from the given request."""
        logger.debug("Running request processing")
        return self.pipelines.request_processing.run(simbot_request)

    def extract_intent_from_user_utterance(self, session: SimBotSession) -> SimBotSession:
        """Determine what the user wants us to do, if anything."""
        # If the user did not say anything, do nothing.
        if not session.current_turn.speech:
            return session

        logger.info(f"[REQUEST] Utterance: `{session.current_turn.speech.utterance}`")

        # Verify user utterance is valid
        session.current_turn.intent.user = self.pipelines.user_utterance_verifier.run(
            session.current_turn.speech
        )

        # If the user has an intent --- i.e. it is not valid --- do not overwrite it.
        if session.current_turn.intent.user is not None:
            return session

        # If the utterance is valid, extract the intent from it.
        logger.debug("Extracting intent from user input...")
        session.current_turn.intent.user = self.pipelines.user_intent_extractor.run(session)

        logger.info(f"[INTENT] User: `{session.current_turn.intent.user}`")
        return session

    def extract_intent_from_environment_feedback(self, session: SimBotSession) -> SimBotSession:
        """Determine what feedback from the environment tells us to do, if anything."""
        logger.debug("Extracting intent from the environment...")
        session.current_turn.intent.environment = self.pipelines.environment_intent_extractor.run(
            session
        )

        logger.info(f"[INTENT] Environment: `{session.current_turn.intent.environment}`")
        return session

    def decide_what_the_agent_should_do(self, session: SimBotSession) -> SimBotSession:
        """Decide what the agent should do next."""
        logger.debug("Selecting agent intent...")
        session.current_turn.intent.agent = self.pipelines.agent_intent_selector.run(session)

        logger.info(f"[INTENT] Agent: `{session.current_turn.intent.agent}`")
        return session

    def generate_interaction_action_if_needed(self, session: SimBotSession) -> SimBotSession:
        """Generate an interaction action for the agent to perform, if needed."""
        if not session.current_turn.intent.should_generate_interaction_action:
            logger.debug(
                "Agent does not need to generate an interaction action for the given intent."
            )
            return session

        logger.debug("Generating interaction action...")
        session.current_turn.actions.interaction = self.pipelines.agent_action_generator.run(
            session
        )

        logger.info(f"[ACTION] Interaction: `{session.current_turn.actions.interaction}`")
        return session

    def generate_language_action_if_needed(self, session: SimBotSession) -> SimBotSession:
        """Generate a language action if needed."""
        logger.debug("Generating utterance for the turn (if needed)...")
        session.current_turn.actions.dialog = self.pipelines.agent_language_generator.run(session)

        logger.info(f"[ACTION] Dialog: `{session.current_turn.actions.dialog}`")
        return session

    def _upload_session_turn_to_database(self, session: SimBotSession) -> None:
        """Upload the current session turn to the database."""
        self.clients.session_db.add_session_turn(session.current_turn)
