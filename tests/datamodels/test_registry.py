import yaml

from emma_experience_hub.constants.simbot import get_service_registry_file_path
from emma_experience_hub.datamodels.registry import ServiceRegistry


def test_service_registry_instantiates_from_yaml() -> None:
    registry_path = get_service_registry_file_path()
    service_registry = ServiceRegistry.parse_obj(yaml.safe_load(registry_path.read_bytes()))

    assert service_registry
