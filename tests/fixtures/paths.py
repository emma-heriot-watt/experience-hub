import os
from pathlib import Path
from typing import Any

from pytest_cases import fixture

from emma_experience_hub.common.settings import SimBotSettings


os.environ["profile"] = "offline"


@fixture(scope="session")
def storage_root() -> Path:
    """Path to the storages root."""
    return Path(__file__).parent.parent.parent.joinpath("storage/")


@fixture(scope="session")
def fixtures_root(storage_root: Path) -> Path:
    """Path to the fixtures storage root."""
    return storage_root.joinpath("fixtures/")


@fixture(scope="session")
def cache_root(request: Any) -> Path:
    """Root of cached dir for the tests."""
    return Path(request.config.cache._cachedir)


@fixture(scope="session")
def auxiliary_metadata_dir(fixtures_root: Path) -> Path:
    """Path to the auxilary game metadata."""
    return fixtures_root.joinpath("simbot/game_metadata/")


@fixture(scope="session")
def auxiliary_metadata_cache_dir(fixtures_root: Path) -> Path:
    """Path to the auxilary the metadata cache."""
    cache_dir = fixtures_root.joinpath("simbot/metadata_cache_dir/")
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


@fixture(scope="session")
def features_cache_dir(fixtures_root: Path) -> Path:
    """Path to the auxilary features cache."""
    features_cache_dir = fixtures_root.joinpath("simbot/features/")
    features_cache_dir.mkdir(exist_ok=True)
    return features_cache_dir


@fixture(scope="session")
def simbot_settings(
    auxiliary_metadata_dir: Path, auxiliary_metadata_cache_dir: Path, features_cache_dir: Path
) -> SimBotSettings:
    """Settings."""
    simbot_settings = SimBotSettings(
        auxiliary_metadata_dir=auxiliary_metadata_dir,
        auxiliary_metadata_cache_dir=auxiliary_metadata_cache_dir,
        extracted_features_cache_dir=features_cache_dir,
    )
    return simbot_settings
