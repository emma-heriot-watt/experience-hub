from pydantic import AnyUrl, BaseSettings, SecretStr


class Settings(BaseSettings):
    """Environment variables which will be needed.

    This class validates the environment variables to ensure they exist.
    """

    github_pat: SecretStr
    log_level: str
    remote_perception_checkpoint_uri: AnyUrl
    remote_policy_checkpoint_uri: AnyUrl
    cuda_version_upper_bound: float = 11.3

    class Config:
        """Config for the Settings."""

        env_file = ".env"
        env_file_encoding = "utf-8"
