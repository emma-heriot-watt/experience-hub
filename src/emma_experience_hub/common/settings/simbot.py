from pydantic import BaseSettings, DirectoryPath


class SimBotSettings(BaseSettings):
    """Settings for the SimBot-related modules."""

    auxiliary_metadata_s3_bucket: str

    auxiliary_metadata_dir: DirectoryPath
    extracted_features_dir: DirectoryPath
    memory_table_name: str = "MEMORY_TABLE"
    db_region_name: str = "us-east-1"

    class Config:
        """Config for the settings."""

        env_prefix = "SIMBOT_"
        env_file = ".env.simbot"
        env_file_encoding = "utf-8"
