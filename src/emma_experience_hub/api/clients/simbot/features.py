from loguru import logger

from emma_experience_hub.api.clients.client import Client
from emma_experience_hub.api.clients.feature_extractor import FeatureExtractorClient
from emma_experience_hub.api.clients.simbot.cache import (
    SimBotAuxiliaryMetadataClient,
    SimBotExtractedFeaturesClient,
)
from emma_experience_hub.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.simbot import SimBotSessionTurn
from emma_experience_hub.datamodels.simbot.payloads import SimBotAuxiliaryMetadataPayload


class SimBotFeaturesClient(Client):
    """Extract features and cache them."""

    def __init__(
        self,
        auxiliary_metadata_cache_client: SimBotAuxiliaryMetadataClient,
        feature_extractor_client: FeatureExtractorClient,
        features_cache_client: SimBotExtractedFeaturesClient,
    ) -> None:
        self._auxiliary_metadata_cache_client = auxiliary_metadata_cache_client
        self._features_cache_client = features_cache_client
        self._feature_extractor_client = feature_extractor_client

    def healthcheck(self) -> bool:
        """Verify all clients are healthy."""
        return all(
            [
                self._auxiliary_metadata_cache_client.healthcheck(),
                self._features_cache_client.healthcheck(),
                self._feature_extractor_client.healthcheck(),
            ]
        )

    def check_exist(self, turn: SimBotSessionTurn) -> bool:
        """Check whether features already exist for the given turn."""
        return self._features_cache_client.check_exist(turn.session_id, turn.prediction_request_id)

    def get_features(self, turn: SimBotSessionTurn) -> list[EmmaExtractedFeatures]:
        """Get the features for the given turn."""
        logger.debug("Getting features for turn...")

        # Try to get from cache
        cache_exists = self.check_exist(turn)

        if cache_exists:
            features = self._features_cache_client.load(
                turn.session_id, turn.prediction_request_id
            )
        else:
            # Extract the features from the cache
            auxiliary_metadata = self._get_auxiliary_metadata(turn)
            features = self._extract_features(auxiliary_metadata)
            # And save them in case they are needed again
            self._features_cache_client.save(features, turn.session_id, turn.prediction_request_id)

        return features

    def _get_auxiliary_metadata(self, turn: SimBotSessionTurn) -> SimBotAuxiliaryMetadataPayload:
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

    def _extract_features(
        self, auxiliary_metadata: SimBotAuxiliaryMetadataPayload
    ) -> list[EmmaExtractedFeatures]:
        """Extract visual features from the given turn."""
        images = auxiliary_metadata.images

        features = (
            self._feature_extractor_client.process_many_images(images)
            if len(images) > 1
            else [self._feature_extractor_client.process_single_image(next(iter(images)))]
        )

        return features
