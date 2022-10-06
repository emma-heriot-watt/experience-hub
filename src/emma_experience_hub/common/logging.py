import logging
import os
from typing import Union

from loguru import logger
from rich.logging import RichHandler
from rich.traceback import install


JSON_LOGS = os.environ.get("JSON_LOGS", "0") == "1"


LOGGER_FORMAT = (
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

RICH_TRACEBACK_SUPRESS_MODULES = ("starlette", "click", "uvicorn")


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


def set_rich_as_default_logger() -> None:
    """Get Rich as the default logger handler."""
    logging.basicConfig(
        format="%(message)s",  # noqa: WPS323
        datefmt="[%X]",  # noqa: WPS323
        handlers=[
            RichHandler(
                markup=True,
                rich_tracebacks=True,
                tracebacks_show_locals=True,
                tracebacks_suppress=RICH_TRACEBACK_SUPRESS_MODULES,
            )
        ],
    )


def setup_api_logging(
    general_log_level: Union[str, int] = "INFO", emma_log_level: Union[str, int] = "INFO"
) -> None:
    """Setup a better loger for the API."""
    # Make sure the log level is all caps
    if isinstance(general_log_level, str):
        general_log_level = general_log_level.upper()

    if isinstance(emma_log_level, str):
        emma_log_level = emma_log_level.upper()

    # intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(general_log_level)

    # remove every other logger's handlers
    # and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

        # Get the log for the emma modules separately
        if name.startswith("emma_"):
            logging.getLogger(name).setLevel(emma_log_level)

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


def get_logger(name: str = "emma_experience_hub") -> logging.Logger:
    """Create and get a Rich logger."""
    set_rich_as_default_logger()
    return logging.getLogger(name)


def enable_rich_tracebacks() -> None:
    """Enable rich tracebacks."""
    install(show_locals=True, suppress=RICH_TRACEBACK_SUPRESS_MODULES)
