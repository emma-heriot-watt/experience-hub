import os
from pathlib import Path

from pytest_cases import fixture


@fixture(scope="session")
def simbot_fixtures_root(fixtures_root: Path) -> Path:
    """Path to the SimBot fixtures."""
    return fixtures_root.joinpath("simbot/")


@fixture
def simbot_game_metadata_dir(simbot_fixtures_root: Path) -> Path:
    """Path to the SimBot game metadata directory."""
    metadata_dir = simbot_fixtures_root.joinpath("game_metadata/")

    # Add to environment variables to handle Settings
    os.environ["SIMBOT_AUXILIARY_METADATA_DIR"] = str(metadata_dir.resolve())

    return metadata_dir
