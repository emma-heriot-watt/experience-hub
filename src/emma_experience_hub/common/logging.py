import logging

from rich.logging import RichHandler
from rich.traceback import install


def get_logger(name: str = "emma_experience_hub") -> logging.Logger:
    """Create and get a Rich logger."""
    # Set the logger to use Rich
    logging.basicConfig(
        format="%(message)s",  # noqa: WPS323
        datefmt="[%X]",  # noqa: WPS323
        handlers=[RichHandler(markup=True, rich_tracebacks=True, tracebacks_show_locals=True)],
    )

    return logging.getLogger(name)


def enable_rich_tracebacks() -> None:
    """Enable rich tracebacks."""
    install(show_locals=True)
