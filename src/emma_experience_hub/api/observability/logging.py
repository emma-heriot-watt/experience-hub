import loguru

from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.datamodels.simbot import SimBotRequest


def create_logger_context(request: SimBotRequest) -> loguru.Contextualizer:
    """Contextualise the logger for the current request."""
    return loguru.logger.contextualize(
        session_id=request.header.session_id,
        prediction_request_id=request.header.prediction_request_id,
    )


def send_logs_to_cloudwatch(
    simbot_settings: SimBotSettings, enable_trace_logging: bool = False
) -> None:
    """Send logs to AWS CloudWatch."""
    try:
        from emma_common.aws.cloudwatch import add_cloudwatch_handler_to_logger  # noqa: WPS433
    except ModuleNotFoundError:
        loguru.logger.warning(
            "Watchtower package not found. Ensure you have installed the package with `poetry install --with production`."
        )
    else:
        add_cloudwatch_handler_to_logger(
            boto3_profile_name=simbot_settings.aws_profile,
            log_stream_name=simbot_settings.watchtower_log_stream_name,
            log_group_name=simbot_settings.watchtower_log_group_name,
            send_interval=1,
            enable_trace_logging=enable_trace_logging,
        )
