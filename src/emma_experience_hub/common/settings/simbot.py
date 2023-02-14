from typing import Optional

from pydantic import AnyHttpUrl, BaseModel, BaseSettings, DirectoryPath, Field, validator

from emma_experience_hub.datamodels.enums import SearchPlannerType


class SimBotFeatureFlags(BaseModel):
    """Feature flags for the SimBot agent."""

    enable_clarification_questions: bool = True
    enable_confirmation_questions: bool = True
    enable_search_actions: bool = True
    enable_grab_from_history: bool = False
    enable_search_after_no_match: bool = True

    enable_always_highlight_before_object_action: bool = False

    search_planner_type: SearchPlannerType = SearchPlannerType.greedy_max_vertex_cover


class SimBotSettings(BaseSettings):
    """Settings for the SimBot-related modules."""

    feature_flags: SimBotFeatureFlags = SimBotFeatureFlags()

    host: str = "0.0.0.0"  # noqa: S104
    port: int = 5000

    client_timeout: Optional[int] = 5

    aws_profile: str = Field(default="TeamProfile", env="aws_profile")

    watchtower_log_group_name: str = "simbot_challenge"
    opensearch_service_name: str = "experience-hub"
    watchtower_log_stream_name: str = "experience-hub/{machine_name}/{logger_name}/{process_id}"

    simbot_cache_s3_bucket: str = "emma-simbot-live-challenge"

    auxiliary_metadata_dir: DirectoryPath
    auxiliary_metadata_cache_dir: DirectoryPath

    extracted_features_cache_dir: DirectoryPath

    session_db_memory_table_name: str = "SIMBOT_MEMORY_TABLE"
    session_db_region: str = "us-east-1"

    feature_extractor_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5500", scheme="http")

    nlu_predictor_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5501", scheme="http")
    nlu_predictor_intent_type_delimiter: str = " "

    profanity_filter_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5503", scheme="http")

    action_predictor_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5502", scheme="http")

    out_of_domain_detector_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5505", scheme="http")

    asr_avg_confidence_threshold: float = 0.55

    confirmation_classifier_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5507", scheme="http")

    compound_splitter_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5508", scheme="http")

    simbot_hacks_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5509", scheme="http")

    otlp_endpoint: AnyHttpUrl = AnyHttpUrl(url="http://localhost:4317", scheme="http")

    class Config:
        """Config for the settings."""

        env_prefix = "SIMBOT_"
        env_file = ".env.simbot"
        env_file_encoding = "utf-8"

    @classmethod
    def from_env(cls) -> "SimBotSettings":
        """Instantiate from the environment variables."""
        return cls.parse_obj({})

    @validator("client_timeout")
    @classmethod
    def fix_timeout(cls, timeout: Optional[int]) -> Optional[int]:
        """Fix the timeout for httpx clients."""
        if timeout is not None and timeout < 0:
            return None

        return timeout
