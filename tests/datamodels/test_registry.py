from pathlib import Path

import yaml
from pytest_cases import fixture

from emma_experience_hub.datamodels.registry import ServiceRegistry


@fixture(scope="module")
def simbot_registry_root(storage_root: Path) -> Path:
    return storage_root.joinpath("registry", "simbot")


def test_service_registry_instantiates_from_yaml(simbot_registry_root: Path) -> None:
    registry_path = simbot_registry_root.joinpath("production.yaml")
    service_registry = ServiceRegistry.parse_obj(yaml.safe_load(registry_path.read_bytes()))

    assert service_registry
