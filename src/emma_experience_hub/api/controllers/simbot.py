import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event
from time import sleep
from typing import Any

from loguru import logger
from opentelemetry import trace
from pydantic import BaseModel

from emma_experience_hub.api.clients import (
    Client,
    CompoundSplitterClient,
    ConfirmationResponseClassifierClient,
    EmmaPolicyClient,
    FeatureExtractorClient,
    OutOfDomainDetectorClient,
    ProfanityFilterClient,
)
from emma_experience_hub.api.clients.simbot import (
    SimbotActionPredictionClient,
    SimBotAuxiliaryMetadataClient,
    SimBotExtractedFeaturesClient,
    SimBotFeaturesClient,
    SimBotSessionDbClient,
    SimBotUtteranceGeneratorClient,
)
from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.datamodels.simbot import (
    SimBotIntentType,
    SimBotRequest,
    SimBotResponse,
    SimBotSession,
    SimBotUserSpeech,
)
from emma_experience_hub.parsers.simbot import (
    SimBotActionPredictorOutputParser,
    SimBotLowASRConfidenceDetector,
    SimBotNLUOutputParser,
    SimBotPreviousActionParser,
    SimBotVisualGroundingOutputParser,
)
from emma_experience_hub.pipelines.simbot import (
    SimBotAgentActionGenerationPipeline,
    SimBotAgentIntentSelectionPipeline,
    SimBotAgentLanguageGenerationPipeline,
    SimBotCompoundSplitterPipeline,
    SimBotEnvironmentIntentExtractionPipeline,
    SimBotFindObjectPipeline,
    SimBotRequestProcessingPipeline,
    SimBotUserIntentExtractionPipeline,
    SimBotUserUtteranceVerificationPipeline,
)


tracer = trace.get_tracer(__name__)


class SimBotControllerClients(BaseModel, arbitrary_types_allowed=True):
    """All the clients for the SimBot Controller API."""

    _exit = Event()

    features: SimBotFeaturesClient
    nlu_intent: EmmaPolicyClient
    action_predictor: SimbotActionPredictionClient
    session_db: SimBotSessionDbClient
    profanity_filter: ProfanityFilterClient
    utterance_generator: SimBotUtteranceGeneratorClient
    out_of_domain_detector: OutOfDomainDetectorClient
    confirmation_response_classifier: ConfirmationResponseClassifierClient
    compound_splitter: CompoundSplitterClient

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
            action_predictor=SimbotActionPredictionClient(
                server_endpoint=simbot_settings.action_predictor_url
            ),
            profanity_filter=ProfanityFilterClient(endpoint=simbot_settings.profanity_filter_url),
            utterance_generator=SimBotUtteranceGeneratorClient.from_templates_file(
                simbot_settings.response_templates
            ),
            out_of_domain_detector=OutOfDomainDetectorClient(
                endpoint=simbot_settings.out_of_domain_detector_url
            ),
            confirmation_response_classifier=ConfirmationResponseClassifierClient(
                endpoint=simbot_settings.confirmation_classifier_url
            ),
            compound_splitter=CompoundSplitterClient(
                endpoint=simbot_settings.compound_splitter_url
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

    @classmethod
    def from_clients(
        cls, clients: SimBotControllerClients, simbot_settings: SimBotSettings
    ) -> "SimBotControllerPipelines":
        """Create the pipelines from the clients."""
        find_object = SimBotFindObjectPipeline(
            features_client=clients.features,
            action_predictor_client=clients.action_predictor,
            visual_grounding_output_parser=SimBotVisualGroundingOutputParser(
                action_delimiter=simbot_settings.action_predictor_delimiter,
                eos_token=simbot_settings.action_predictor_eos_token,
            ),
        )

        action_predictor_response_parser = SimBotActionPredictorOutputParser(
            action_delimiter=simbot_settings.action_predictor_delimiter,
            eos_token=simbot_settings.action_predictor_eos_token,
        )

        return cls(
            compound_splitter=SimBotCompoundSplitterPipeline(clients.compound_splitter),
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
                confirmation_response_classifier=clients.confirmation_response_classifier,
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
                action_predictor_client=clients.action_predictor,
                _disable_clarification_questions=simbot_settings.disable_clarification_questions,
                _disable_search_actions=simbot_settings.disable_search_actions,
            ),
            agent_action_generator=SimBotAgentActionGenerationPipeline(
                features_client=clients.features,
                action_predictor_client=clients.action_predictor,
                action_predictor_response_parser=action_predictor_response_parser,
                previous_action_parser=SimBotPreviousActionParser(),
                find_object_pipeline=find_object,
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
        session = self._clear_queue_if_needed(session)
        # session = self.split_utterance_if_needed(session)
        session = self.get_utterance_from_queue_if_needed(session)
        session = self.extract_intent_from_user_utterance(session)
        session = self.extract_intent_from_environment_feedback(session)
        session = self.decide_what_the_agent_should_do(session)
        session = self.generate_interaction_action_if_needed(session)
        session = self.generate_language_action_if_needed(session)

        self._upload_session_turn_to_database(session)

        return session.current_turn.convert_to_simbot_response()

    def split_utterance_if_needed(self, session: SimBotSession) -> SimBotSession:
        """Tries to split the utterance in case we are dealing with a complex instruction."""
        if session.current_turn.intent.user is not None:
            logger.debug("Current turn already has user intent; utterance will not be split.")
            return session

        logger.debug("Trying to split the instruction...")
        with tracer.start_as_current_span("Split compound utterance"):
            return self.pipelines.compound_splitter.run(session)

    def load_session_from_request(self, simbot_request: SimBotRequest) -> SimBotSession:
        """Load the entire session from the given request."""
        logger.debug("Running request processing")

        with tracer.start_as_current_span("Load session from request"):
            session = self.pipelines.request_processing.run(simbot_request)

        # Verify user utterance is valid
        if simbot_request.speech_recognition:
            with tracer.start_as_current_span("Verify incoming utterance"):
                user_intent = self.pipelines.user_utterance_verifier.run(
                    simbot_request.speech_recognition
                )
                session.current_turn.intent.user = user_intent

        return session

    def extract_intent_from_user_utterance(self, session: SimBotSession) -> SimBotSession:
        """Determine what the user wants us to do, if anything."""
        # If the user did not say anything, do nothing.
        if not session.current_turn.speech:
            return session

        logger.info(f"[REQUEST] Utterance: `{session.current_turn.speech.utterance}`")

        # If the user has an intent --- i.e. it is not valid --- do not overwrite it.
        if session.current_turn.intent.user:
            logger.debug(
                f"User intent (`{session.current_turn.intent.user}`) already exists for turn; using that."
            )
            return session

        # If the utterance is valid, extract the intent from it.
        logger.debug("Extracting intent from user input...")

        with tracer.start_as_current_span("Extract intent from user utterance"):
            user_intent = self.pipelines.user_intent_extractor.run(session)

        logger.info(f"[INTENT] User: `{user_intent}`")

        # If the user wants us to act, reset the queue
        if user_intent is not None and user_intent == SimBotIntentType.act:
            logger.debug(
                "User has given us a new instruction to act on. Therefore, reset the queue."
            )
            session.current_state.utterance_queue.reset()

        session.current_turn.intent.user = user_intent
        return session

    def extract_intent_from_environment_feedback(self, session: SimBotSession) -> SimBotSession:
        """Determine what feedback from the environment tells us to do, if anything."""
        logger.debug("Extracting intent from the environment...")

        with tracer.start_as_current_span("Extract intent from environment feedback"):
            session.current_turn.intent.environment = (
                self.pipelines.environment_intent_extractor.run(session)
            )

        logger.info(f"[INTENT] Environment: `{session.current_turn.intent.environment}`")
        return session

    def get_utterance_from_queue_if_needed(self, session: SimBotSession) -> SimBotSession:
        """Check the queue to see if there is an utterance that needs to be handled."""
        # If user intent exists for the current turn, do not try to replace it.
        if session.current_turn.intent.user is not None:
            return session

        if not session.current_turn.speech:
            return session

        should_get_utterance_from_queue = [
            # Queue must not be empty
            session.current_state.utterance_queue,
            # Previous action must end in end-of-trajectory token
            session.previous_turn
            and session.previous_turn.actions.interaction
            and session.previous_turn.actions.interaction.is_end_of_trajectory,
        ]

        # Pop the utterance from the queue and add it to the turn
        if all(should_get_utterance_from_queue):
            logger.info(
                f"[REQUEST]: Get utterance from the session queue ({len(session.current_state.utterance_queue) - 1} remaining"
            )
            session.current_turn.speech = SimBotUserSpeech(
                utterance=session.current_state.utterance_queue.pop_from_head()
            )

        return session

    def decide_what_the_agent_should_do(self, session: SimBotSession) -> SimBotSession:
        """Decide what the agent should do next."""
        logger.debug("Selecting agent intent...")
        with tracer.start_as_current_span("Determine agent intent"):
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

        # The raw text match has failed to match the user utterance into a single action
        # Therefore, there is no interaction for the current turn, try to fill it
        if session.current_turn.actions.interaction is None:
            logger.debug("Generating interaction action...")
            with tracer.start_as_current_span("Generate interaction action"):
                session.current_turn.actions.interaction = (
                    self.pipelines.agent_action_generator.run(session)
                )

        logger.info(f"[ACTION] Interaction: `{session.current_turn.actions.interaction}`")
        return session

    def generate_language_action_if_needed(self, session: SimBotSession) -> SimBotSession:
        """Generate a language action if needed."""
        logger.debug("Generating utterance for the turn (if needed)...")

        with tracer.start_as_current_span("Generate utterance"):
            session.current_turn.actions.dialog = self.pipelines.agent_language_generator.run(
                session
            )

        logger.info(f"[ACTION] Dialog: `{session.current_turn.actions.dialog}`")
        return session

    def _upload_session_turn_to_database(self, session: SimBotSession) -> None:
        """Upload the current session turn to the database."""
        self.clients.session_db.add_session_turn(session.current_turn)

    def _clear_queue_if_needed(self, session: SimBotSession) -> SimBotSession:
        """Clear the queue if the user has provided us with a new instruction."""
        if session.current_turn.speech:
            logger.debug("[REQUEST]: Received utterance from user; clearing the utterance queue")
            session.current_state.utterance_queue.reset()

        return session
