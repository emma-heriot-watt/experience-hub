from pydantic import BaseSettings


class Settings(BaseSettings):
    """Environment variables which will be needed.

    This class validates the environment variables to ensure they exist.
    """

    # github_pat: SecretStr
    log_level: str = "debug"

    # remote_perception_checkpoint_uri: AnyUrl
    # remote_policy_checkpoint_uri: AnyUrl
    cuda_version_upper_bound: float = 11.3

    # Repository directories
    # perception_repo_root: DirectoryPath
    # perception_python_executable: FilePath

    # policy_repo_root: DirectoryPath
    # policy_python_executable: FilePath

    class Config:
        """Config for the Settings."""

        env_file = ".env"
        env_file_encoding = "utf-8"

    @classmethod
    def from_env(cls) -> "Settings":
        """Instantiate from the environment variables."""
        return cls.parse_obj({})
