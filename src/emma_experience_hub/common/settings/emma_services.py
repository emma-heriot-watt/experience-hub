from pydantic import BaseSettings


class EmmaServiceSettings(BaseSettings):
    """Settings for external services (i.e. Docker containers)."""

    # Ports
    feature_extractor_port: int = 5500

    # Common running configs
    model_dir_within_container: str = "/app/models"
    log_level: str = "DEBUG"
