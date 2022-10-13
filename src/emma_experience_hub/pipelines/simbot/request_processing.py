from loguru import logger

from emma_experience_hub.api.clients import FeatureExtractorClient
from emma_experience_hub.api.clients.simbot import SimBotCacheClient, SimBotSessionDbClient
from emma_experience_hub.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.simbot import (
    SimBotActionStatus,
    SimBotRequest,
    SimBotSession,
    SimBotSessionTurn,
)
from emma_experience_hub.datamodels.simbot.payloads import SimBotAuxiliaryMetadataPayload


class SimBotRequestProcessingPipeline:
    """Process the incoming requests and build the session data."""

    def __init__(
        self,
        feature_extractor_client: FeatureExtractorClient,
        auxiliary_metadata_cache_client: SimBotCacheClient[SimBotAuxiliaryMetadataPayload],
        extracted_features_cache_client: SimBotCacheClient[list[EmmaExtractedFeatures]],
        session_db_client: SimBotSessionDbClient,
    ) -> None:
        self._feature_extractor_client = feature_extractor_client

        self._auxiliary_metadata_cache_client = auxiliary_metadata_cache_client
        self._extracted_features_cache_client = extracted_features_cache_client

        self._session_db_client = session_db_client

    def run(self, request: SimBotRequest) -> SimBotSession:
        """Run the pipeline for the current request."""
        # Get all the previous turns for the history
        session_history = self.get_session_history(request.header.session_id)

        if session_history:
            self.update_previous_turn_with_action_status(
                session_history[-1], request.request.previous_actions
            )

        # Create a turn for the current request and update the history
        session_history.append(
            SimBotSessionTurn.new_from_simbot_request(request, idx=len(session_history))
        )

        # TODO: Does checking cached features exist for all frames lead cause a latency problem?
        # How can we track the latency of the entire pipeline?

        # Check that frames have been extracted for all the turns
        self.validate_extracted_features_for_session(session_history)

        return SimBotSession(session_id=request.header.session_id, turns=session_history)

    def get_session_history(self, session_id: str) -> list[SimBotSessionTurn]:
        """Get the history for the session.

        This should use an API client to pull the history for the given session.
        """
        return self._session_db_client.get_all_session_turns(session_id)

    def update_previous_turn_with_action_status(
        self, turn: SimBotSessionTurn, action_status: list[SimBotActionStatus]
    ) -> None:
        """Update the previous turn with the action status.

        We are assuming that the order of actions is the exact same as the order of action
        statuses.
        """
        if not action_status:
            logger.warning(
                "Previous action status is empty, therefore cannot update status of previous session turn. Moving on..."
            )
            return

        if turn.action is None:
            logger.error("The turn should have an action. Is this the right turn?")
            return

        if len(action_status) > 1:
            logger.error(
                f"The number of actions with the turn is not equal to the number of statuses available. There is only 1 action within the turn, but {len(action_status)} statuses."
            )
            logger.warning(
                "Trying to match the available actions to the available statuses anyway."
            )

        # Update the action status, ensuring we match the right one.
        for status in action_status:
            if status.type == turn.action.type.base_type:
                turn.action.status = status

        # Put the updated session turn into the db
        self._session_db_client.put_session_turn(turn)

    def validate_extracted_features_for_session(self, turns: list[SimBotSessionTurn]) -> None:
        """Check existance for all turns, and extract features if they do not exist."""
        for turn in turns:
            self._validate_session_turn_features_are_cached(turn)

            # with ThreadPoolExecutor() as pool:
        # pool.map(self._validate_session_turn_features_are_cached, turns)

    def _validate_session_turn_features_are_cached(self, turn: SimBotSessionTurn) -> bool:
        """Validate the session turn and ensure that the features are extracted and cached."""
        cache_exists = self._extracted_features_cache_client.check_exist(
            turn.session_id, turn.prediction_request_id
        )

        if not cache_exists:
            # Get auxiliary metadata for the turn
            auxiliary_metadata = self._get_auxiliary_metadata_for_turn(turn)

            # Extract features and save them
            extracted_features = self._extract_features_from_session_turn(auxiliary_metadata)
            self._extracted_features_cache_client.save(
                extracted_features, turn.session_id, turn.prediction_request_id
            )

        cache_exists = self._extracted_features_cache_client.check_exist(
            turn.session_id, turn.prediction_request_id
        )

        if not cache_exists:
            # TODO: is this the best way to handle this?
            raise FileNotFoundError("Something went wrong and the features were not cached.")

        return cache_exists

    def _get_auxiliary_metadata_for_turn(
        self, turn: SimBotSessionTurn
    ) -> SimBotAuxiliaryMetadataPayload:
        """Cache the auxiliary metadata for the given turn."""
        # Check whether the auxiliary metadata exists within the cache
        auxiliary_metadata_exists = self._auxiliary_metadata_cache_client.check_exist(
            turn.session_id, turn.prediction_request_id
        )

        # Load the auxiliary metadata from the cache or the EFS URi
        auxiliary_metadata = (
            self._auxiliary_metadata_cache_client.load(turn.session_id, turn.prediction_request_id)
            if auxiliary_metadata_exists
            else SimBotAuxiliaryMetadataPayload.from_efs_uri(uri=turn.auxiliary_metadata_uri)
        )

        # If it has not been cached, upload it to the cache
        if not auxiliary_metadata_exists:
            self._auxiliary_metadata_cache_client.save(
                auxiliary_metadata,
                turn.session_id,
                turn.prediction_request_id,
            )

        return auxiliary_metadata

    def _extract_features_from_session_turn(
        self, auxiliary_metadata: SimBotAuxiliaryMetadataPayload
    ) -> list[EmmaExtractedFeatures]:
        """Extract visual features from the given turn."""
        if not self._feature_extractor_client.healthcheck():
            # TODO: Is this the best way to handle this?
            raise AssertionError("Feature extractor is not currently available.")

        images = auxiliary_metadata.images

        features = (
            self._feature_extractor_client.process_many_images(images)
            if len(images) > 1
            else [self._feature_extractor_client.process_single_image(next(iter(images)))]
        )

        return features
