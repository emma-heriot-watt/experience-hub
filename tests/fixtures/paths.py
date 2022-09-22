from pathlib import Path

from pytest_cases import fixture


@fixture
def fixtures_root() -> Path:
    """Path to the fixtures storage root."""
    return Path(__file__).parent.parent.parent.joinpath("storage", "fixtures/")
