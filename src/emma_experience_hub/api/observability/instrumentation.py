from fastapi import FastAPI
from loguru import logger

from emma_experience_hub.common.settings import SimBotSettings


def instrument_app(fastapi_app: FastAPI, simbot_settings: SimBotSettings) -> None:
    """Prepare the FastAPI app."""
    try:
        from emma_common.api.instrumentation import (  # noqa: WPS433
            instrument_fastapi_app,
            setup_tracing,
        )
    except ImportError:
        logger.warning(
            "Unable to instrument FastAPI app. This warning can be ignored if you are NOT running in production."
        )
        return

    setup_tracing(
        service_name=simbot_settings.opensearch_service_name,
        otlp_endpoint=simbot_settings.otlp_endpoint,
    )
    instrument_fastapi_app(fastapi_app)

    logger.info("Application instrumented successfully.")
