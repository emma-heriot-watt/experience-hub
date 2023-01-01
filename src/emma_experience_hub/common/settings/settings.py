from pydantic import BaseSettings


class Settings(BaseSettings):
    """Environment variables which will be needed."""

    log_level: str = "debug"

    cuda_version_upper_bound: float = 11.3

    class Config:
        """Config for the Settings."""

        env_file = ".env"
        env_file_encoding = "utf-8"

    @classmethod
    def from_env(cls) -> "Settings":
        """Instantiate from the environment variables."""
        return cls.parse_obj({})
