import logging
import os
from typing import Union

from loguru import logger
from rich.logging import RichHandler


JSON_LOGS = os.environ.get("JSON_LOGS", "0") == "1"
EMMA_LOG_LEVEL = logging.getLevelName(os.environ.get("LOG_LEVEL", "DEBUG").upper())

LOGGER_FORMAT = (
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

RICH_TRACEBACK_SUPRESS_MODULES = ("starlette", "click", "uvicorn", "fastapi")


class InterceptHandler(logging.Handler):
    """Logger Handler to intercept log messages from all callers."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit method for logging."""
        # Get corresponding Loguru level if it exists
        level: Union[str, int]

        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2

        while frame.f_code.co_filename == logging.__file__:
            if frame.f_back is not None:
                frame = frame.f_back
                depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(_default_log_level: str = "INFO") -> None:
    """Setup a better logger for the API."""
    # intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.getLevelName(_default_log_level))

    # remove every other logger's handlers
    # and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

        # Get the log for the emma modules separately
        if name.startswith("emma_"):
            logging.getLogger(name).setLevel(EMMA_LOG_LEVEL)

    # configure loguru
    logger.configure(
        handlers=[
            {
                "sink": RichHandler(
                    markup=True,
                    rich_tracebacks=True,
                    tracebacks_show_locals=True,
                    tracebacks_suppress=RICH_TRACEBACK_SUPRESS_MODULES,
                ),
                "format": LOGGER_FORMAT,
                "serialize": JSON_LOGS,
            }
        ]
    )
