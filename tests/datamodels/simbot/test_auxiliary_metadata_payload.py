from pathlib import Path

import pytest
from PIL import Image
from pydantic import BaseModel, ValidationError
from pytest_cases import parametrize

from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotAuxiliaryMetadata,
    SimBotAuxiliaryMetadataUri,
)


class ExampleUrlModel(BaseModel):
    uri: SimBotAuxiliaryMetadataUri


@parametrize(
    "uri",
    [
        "efs://sample-game-metadata.json",
        pytest.param(
            "file://sample-game-metadata.json", marks=pytest.mark.xfail(raises=ValidationError)
        ),
    ],
)
def test_game_metadata_uri_field_can_be_instantiated(uri: str) -> None:
    test_model = ExampleUrlModel.parse_obj({"uri": uri})
    assert test_model.uri
    assert test_model.uri.scheme == "efs"
    assert test_model.uri.tld == "json"


def test_game_metadata_uri_field_can_resolve_to_local_path(simbot_game_metadata_dir: Path) -> None:
    test_model = ExampleUrlModel.parse_obj({"uri": "efs://sample-game-metadata.json"})
    assert test_model.uri

    resolved_path = test_model.uri.resolve_path(simbot_game_metadata_dir)

    assert resolved_path.exists()
    assert resolved_path.is_file()


def test_game_metadata_loads_from_json(simbot_game_metadata_dir: Path) -> None:
    resolved_path = ExampleUrlModel.parse_obj(
        {"uri": "efs://sample-game-metadata.json"}
    ).uri.resolve_path(simbot_game_metadata_dir)

    # Load the metadata from the json file
    metadata = SimBotAuxiliaryMetadata.parse_file(resolved_path)

    # Verify the properties
    # assert metadata.current_room
    # assert metadata.unique_room_names

    # Verify the images get parsed without errors
    for image in metadata.images:
        assert isinstance(image, Image.Image)
