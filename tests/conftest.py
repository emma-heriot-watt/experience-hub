import os
from glob import glob
from pathlib import Path

import pytest


# Import all the fixtures from every file in the tests/fixtures dir.
pytest_plugins = [
    fixture_file.replace("/", ".").replace(".py", "")
    for fixture_file in glob("tests/fixtures/[!__]*.py", recursive=True)
]

os.environ["RUNNING_TESTS"] = "1"

STORAGE_ROOT = Path("storage")
FIXTURES_ROOT = STORAGE_ROOT.joinpath("fixtures/")
SIMBOT_FIXTURES_ROOT = FIXTURES_ROOT.joinpath("simbot/")

# Add to environment variables to handle Settings
os.environ["SIMBOT_AUXILIARY_METADATA_DIR"] = str(
    SIMBOT_FIXTURES_ROOT.joinpath("game_metadata/").resolve()
)
os.environ["SIMBOT_AUXILIARY_METADATA_CACHE_DIR"] = str(
    SIMBOT_FIXTURES_ROOT.joinpath("game_metadata/").resolve()
)
os.environ["SIMBOT_EXTRACTED_FEATURES_CACHE_DIR"] = str(
    SIMBOT_FIXTURES_ROOT.joinpath("features/").resolve()
)


if os.getenv("_PYTEST_RAISE", "0") != "0":

    @pytest.hookimpl(tryfirst=True)
    def pytest_exception_interact(call):
        raise call.excinfo.value

    @pytest.hookimpl(tryfirst=True)
    def pytest_internalerror(excinfo):
        raise excinfo.value
