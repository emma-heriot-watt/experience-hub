from dotenv import load_dotenv
from pydantic import AnyUrl, BaseSettings, SecretStr, ValidationError

from emma_experience_hub.common.logging import get_logger


log = get_logger()


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


def load_env_vars() -> None:
    """Load the environment variables from the `.env` file and verify them."""
    load_dotenv()

    try:
        Settings()
    except ValidationError as exception:
        log.exception(exception)
        log.error(
            "Could not load environment variables.",
            "Do you have a `[bright_cyan u].env[/]` file?",
        )


if __name__ == "__main__":
    load_env_vars()
