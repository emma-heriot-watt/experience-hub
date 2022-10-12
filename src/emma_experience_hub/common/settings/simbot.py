from pydantic import AnyHttpUrl, BaseSettings, DirectoryPath


class SimBotSettings(BaseSettings):
    """Settings for the SimBot-related modules."""

    app_name: str = "EMMA SimBot API"
    host: str = "0.0.0.0"  # noqa: S104
    port: int = 5000

    auxiliary_metadata_s3_bucket: str = "emma-simbot-live-bucket"
    auxiliary_metadata_cache_dir: DirectoryPath
    auxiliary_metadata_dir: DirectoryPath

    extracted_features_dir: DirectoryPath

    session_db_memory_table_name: str = "SIMBOT_MEMORY_TABLE"
    session_db_region: str = "us-east-1"

    feature_extractor_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5500", scheme="http")

    # NLU settings
    nlu_predictor_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5501", scheme="http")
    nlu_predictor_intent_type_delimiter: str = " "

    profanity_filter_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5503", scheme="http")

    utterance_generator_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5504", scheme="http")

    # Action predictor settings
    action_predictor_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5502", scheme="http")
    action_predictor_delimiter: str = "."
    action_predictor_eos_token: str = "</s>"

    out_of_domain_detector_url: AnyHttpUrl = AnyHttpUrl(url="http://0.0.0.0:5505", scheme="http")

    class Config:
        """Config for the settings."""

        env_prefix = "SIMBOT_"
        env_file = ".env.simbot"
        env_file_encoding = "utf-8"

    @classmethod
    def from_env(cls) -> "SimBotSettings":
        """Instantiate from the environment variables."""
        return cls.parse_obj({})
