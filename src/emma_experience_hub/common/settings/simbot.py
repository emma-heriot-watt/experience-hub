from typing import Optional

from pydantic import AnyHttpUrl, BaseSettings, DirectoryPath, Field, validator


class SimBotSettings(BaseSettings):
    """Settings for the SimBot-related modules."""

    # Feature flags
    disable_clarification_questions: bool = False
    disable_clarification_confirmation: bool = True
    disable_search_actions: bool = False
    disable_grab_from_history: bool = True
    find_planner_type: str = "greedy_max_vertex_cover"

    host: str = "0.0.0.0"  # noqa: S104
    port: int = 5000

    client_timeout: Optional[int] = 5

    aws_profile: str = Field(default="TeamProfile", env="aws_profile")

    watchtower_log_group_name: str = "simbot_challenge"
    watchtower_log_stream_name: str = "{machine_name}/{logger_name}/{process_id}"

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
    action_predictor_delimiter: str = "."
    action_predictor_eos_token: str = "</s>"

    out_of_domain_detector_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5505", scheme="http")

    asr_avg_confidence_threshold: float = 0.55

    confirmation_classifier_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5507", scheme="http")

    compound_splitter_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5508", scheme="http")

    otlp_endpoint: AnyHttpUrl = AnyHttpUrl(url="http://localhost:4317", scheme="http")

    opensearch_service_name: str = "experience-hub"

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
