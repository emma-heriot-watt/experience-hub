from contextlib import suppress

from loguru import logger
from opentelemetry import trace

from emma_common.datamodels import SpeakerRole
from emma_experience_hub.api.controllers.simbot.clients import SimBotControllerClients
from emma_experience_hub.api.controllers.simbot.pipelines import SimBotControllerPipelines
from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.datamodels.simbot import (
    SimBotIntentType,
    SimBotRequest,
    SimBotResponse,
    SimBotSession,
    SimBotUserSpeech,
)


tracer = trace.get_tracer(__name__)


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
        session = self.split_utterance_if_needed(session)
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

        # Current speech is from agent planner
        speech_from_planner = (
            session.current_turn.speech is None
            or session.current_turn.speech.role == SpeakerRole.agent
        )
        if speech_from_planner:
            logger.debug("Current turn is executing an utterance from the planner.")
            return session

        logger.debug("Trying to split the instruction...")
        with tracer.start_as_current_span("Split compound utterance"):
            session = self.pipelines.compound_splitter.run(session)
            return self.pipelines.compound_splitter.run_coreference_resolution(session)

    def load_session_from_request(self, simbot_request: SimBotRequest) -> SimBotSession:
        """Load the entire session from the given request."""
        logger.debug("Running request processing")

        with tracer.start_as_current_span("Load session from request"):
            session = self.pipelines.request_processing.run(simbot_request)

        # Verify user utterance is valid
        if self.settings.is_not_offline_evaluation and simbot_request.speech_recognition:
            with tracer.start_as_current_span("Verify incoming utterance"):
                user_intent = self.pipelines.user_utterance_verifier.run(
                    simbot_request.speech_recognition
                )
                session.current_turn.intent.user = user_intent

        # Cache the auxiliary metadata for the turn
        self.clients.features.get_auxiliary_metadata(session.current_turn)

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
            if session.current_state.last_user_utterance.is_not_empty:
                session.current_state.last_user_utterance.pop_from_head()
            return session

        # If the utterance is valid, extract the intent from it.
        logger.debug("Extracting intent from user input...")

        with tracer.start_as_current_span("Extract intent from user utterance"):
            user_intent = self.pipelines.user_intent_extractor.run(session)

        logger.info(f"[INTENT] User: `{user_intent}`")
        user_intent_is_not_act = user_intent != SimBotIntentType.act
        if user_intent_is_not_act and session.current_state.last_user_utterance.is_not_empty:
            session.current_state.last_user_utterance.pop_from_head()

        session.current_turn.intent.user = user_intent
        return self._clear_queue_after_user_intent(session)

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

        if session.current_turn.speech:
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
            queue_elem = session.current_state.utterance_queue.pop_from_head()
            session.current_turn.speech = SimBotUserSpeech.update_user_utterance(
                utterance=queue_elem.utterance,
                from_utterance_queue=True,
                role=queue_elem.role,
            )

        return session

    def decide_what_the_agent_should_do(self, session: SimBotSession) -> SimBotSession:
        """Decide what the agent should do next."""
        logger.debug("Selecting agent intent...")
        with tracer.start_as_current_span("Determine agent intent"):
            agent_intents = self.pipelines.agent_intent_selector.run(session)

            session.current_turn.intent.physical_interaction = agent_intents[0]
            session.current_turn.intent.verbal_interaction = agent_intents[1]

        logger.info(f"[INTENT] Interaction: `{session.current_turn.intent.physical_interaction}`")
        logger.info(
            f"[INTENT] Language Condition: `{session.current_turn.intent.verbal_interaction}`"
        )
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

            with tracer.start_as_current_span("Anticipate instructions"):
                self.pipelines.anticipator.run(session)

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

    @tracer.start_as_current_span("Upload cache to S3")
    def upload_cache_to_s3(self, session_id: str, prediction_request_id: str) -> None:
        """Upload the cached data to S3.

        If the file does not exist, we don't care so just suppress that exception.
        """
        # Dont upload anything to s3
        return None
        with suppress(FileNotFoundError):
            self.clients.features.auxiliary_metadata_cache_client.upload_to_s3(
                session_id, prediction_request_id
            )
            self.clients.features.features_cache_client.upload_to_s3(
                session_id, prediction_request_id
            )

    def _upload_session_turn_to_database(self, session: SimBotSession) -> None:
        """Upload the current session turn to the database."""
        self.clients.session_db.add_session_turn(session.current_turn)

    def _clear_queue_if_needed(self, session: SimBotSession) -> SimBotSession:
        """Clear the queue if the user has provided us with a new instruction.

        That means if there is speech in the current turn and that is not in response to a
        question.
        """
        if session.current_turn.speech:
            # Reset the queues if
            reset_conditions = [
                # 1) the current turn has an invalid utterance or
                self._new_utterance_is_invalid(session),
                # 2) is valid and not responding to a previous question
                not self._user_is_responding_to_question(session),
            ]
            if any(reset_conditions):
                logger.debug("[REQUEST]: Received utterance; clearing queues")
                session.current_state.utterance_queue.reset()
                session.current_state.find_queue.reset()
                return session

        return session

    def _clear_queue_after_user_intent(self, session: SimBotSession) -> SimBotSession:
        """Clear the queue if the user has provided us with a new instruction.

        After the confirmation classifier, check if the user replied to a confirmation question
        with a confirmation response or a new instruction.
        """
        new_instruction_after_confirmation = [
            # We previously asked for confirmation
            session.previous_turn is not None
            and session.previous_turn.intent.verbal_interaction is not None
            and session.previous_turn.intent.verbal_interaction.type.triggers_confirmation_question,
            # But the user intent is not a confirmation response
            session.current_turn.intent.user is not None
            and not session.current_turn.intent.user.is_confirmation_response,
        ]
        if all(new_instruction_after_confirmation):
            logger.debug(
                "[REQUEST]: Received instruction utterance after confirmation; clearing the utterance queue"
            )
            session.current_state.utterance_queue.reset()
            session.current_state.find_queue.reset()

        return session

    def _new_utterance_is_invalid(self, session: SimBotSession) -> bool:
        """Return True if the user is current utterance is invalid."""
        return (
            session.current_turn.intent.user is not None
            and session.current_turn.intent.user.is_invalid_user_utterance
        )

    def _user_is_responding_to_question(self, session: SimBotSession) -> bool:
        """Return True if the user is responding to question from previous turn."""
        return (
            session.previous_turn is not None
            and session.previous_turn.intent.agent_should_ask_question_to_user
        )
