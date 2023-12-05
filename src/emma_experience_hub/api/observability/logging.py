from __future__ import annotations

import loguru

from emma_experience_hub.datamodels.simbot import SimBotRequest


def create_logger_context(request: SimBotRequest) -> loguru.Contextualizer:
    """Contextualise the logger for the current request."""
    return loguru.logger.contextualize(
        session_id=request.header.session_id,
        prediction_request_id=request.header.prediction_request_id,
    )
