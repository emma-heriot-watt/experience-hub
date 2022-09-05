import logging

from rich.logging import RichHandler


def get_logger(name: str = "emma_experience_hub") -> logging.Logger:
    """Create and get a Rich logger."""
    # Set the logger to use Rich
    logging.basicConfig(
        format="%(message)s",  # noqa: WPS323
        datefmt="[%X]",  # noqa: WPS323
        handlers=[RichHandler(markup=True, rich_tracebacks=True)],
    )

    return logging.getLogger(name)
