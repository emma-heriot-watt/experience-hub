from starlite import Response, State, post

from emma_experience_hub.api.clients import (
    FeatureExtractorClient,
    SimBotAuxiliaryMetadataS3Client,
    SimBotExtractedFeaturesFileSystemClient,
)
from emma_experience_hub.common.settings import Settings, SimBotSettings
from emma_experience_hub.datamodels.simbot import SimBotRequest, SimBotResponse
from emma_experience_hub.pipelines import RequestProcessingPipeline


settings = Settings()


def handle_application_startup(state: State) -> None:
    """Handle the startup of the API."""
    simbot_settings = SimBotSettings()

    # Start all docker containers

    # TODO: Start feature extractor API

    # TODO: Start NLU API server

    # TODO: Start next action prediction server

    # TODO: Ensure that they are all running

    # TODO: Ensure that they are all accessible

    # TODO: Create all the API pipelines
    # API Clients
    state.clients.feature_extractor = FeatureExtractorClient()
    state.clients.auxiliary_metadata_cache = SimBotAuxiliaryMetadataS3Client(
        bucket_name=simbot_settings.auxiliary_metadata_s3_bucket,
        local_backup_root_path=simbot_settings.auxiliary_metadata_dir,
    )
    state.clients.extracted_features_cache = SimBotExtractedFeaturesFileSystemClient(
        root_directory=simbot_settings.extracted_features_dir
    )

    # Create pipelines
    state.pipelines.request_processing = RequestProcessingPipeline(
        feature_extractor_client=state.clients.feature_extractor,
        auxiliary_metadata_cache_client=state.clients.auxiliary_metadata_cache,
        extracted_features_cache_client=state.clients.extracted_features_cache,
    )

    # TODO: Submit log that application is ready


@post("/predict")
def handle_request(state: State, reuqest: SimBotRequest) -> Response[SimBotResponse]:
    """Handle a new request from the SimBot API."""
    response = SimBotResponse()

    return response.dict(by_alias=True)
