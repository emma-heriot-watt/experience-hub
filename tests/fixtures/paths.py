from pathlib import Path
from typing import Any

from pytest_cases import fixture


@fixture(scope="session")
def fixtures_root() -> Path:
    """Path to the fixtures storage root."""
    return Path(__file__).parent.parent.parent.joinpath("storage", "fixtures/")


@fixture(scope="session")
def cache_root(request: Any) -> Path:
    """Root of cached dir for the tests."""
    return Path(request.config.cache._cachedir)
