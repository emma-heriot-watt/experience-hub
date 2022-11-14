from base64 import b64decode
from io import BytesIO
from pathlib import Path
from typing import Any

import orjson
from PIL import Image
from pydantic import AnyUrl, BaseModel, Field, FilePath, root_validator

from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.datamodels.simbot.payloads.payload import SimBotPayload


class SimBotAuxiliaryMetadataUri(AnyUrl):
    """Game Metadata URI for the SimBot game.

    This should validate and convert the path for the local system.
    """

    allowed_schemes = {"efs"}
    host_required = False

    __slots__ = ()

    def resolve_path(self, game_metadata_efs_dir: Path) -> FilePath:
        """Fully resolve the path to the game metadata file.

        This follows the provided example:
        https://us-east-1.console.aws.amazon.com/codesuite/codecommit/repositories/AlexaSimbotModelInferenceService/browse/refs/heads/main/--/alexa_simbot_action_inference_model_wrapper/service/models/V103.py?region=us-east-1&lines=1479-1481
        """
        # Perform the replace as they've done (from the example)
        efs_dir_as_string = str(game_metadata_efs_dir.resolve())
        corrected_image_uri = self.replace("efs://", f"{efs_dir_as_string}/")

        game_metadata_path = Path(corrected_image_uri)

        # Verify the path exists
        if not game_metadata_path.exists():
            raise FileNotFoundError(
                "Game metadata file does not exist at ", game_metadata_path.resolve()
            )

        return game_metadata_path


class SimBotAuxiliaryMetadataRobotInfo(BaseModel):
    """SimBot Robot info for the current image."""

    current_room: str = Field(..., alias="currentRoom")


class SimBotAuxiliaryMetadata(BaseModel):
    """SimBot Image data provided for each request made."""

    encoded_images: dict[int, str] = Field(..., alias="colorImages")
    # TODO: Disabled due to Arena v3 changes
    # robot_info: list[SimBotAuxiliaryMetadataRobotInfo] = Field(..., alias="robotInfo", min_items=1)
    # viewpoints: set[str] = Field(..., alias="viewPoints")

    @property
    def images(self) -> list[Image.Image]:
        """Decode the base-64 encoded strings into images.

        Because dictionaries are not strictly ordered, we need to make sure we get the images in
        the correct order.
        """
        ordered_encoded_images = sorted(self.encoded_images.items())
        decoded_images = [
            Image.open(BytesIO(b64decode(image_str))) for _, image_str in ordered_encoded_images
        ]
        return decoded_images

    # @property
    # def current_room(self) -> str:
    #     """Get the robot's current room.

    #     According to their source code, there is only going to be one item in this list. Therefore,
    #     we can do this.
    #     """
    #     if len(self.robot_info) > 1:
    #         logger.warning("There is more than one `current_room` within the `robotInfo` field")

    #     return next(iter(self.robot_info)).current_room

    # @property
    # def unique_room_names(self) -> set[str]:
    #     """Get the unique room names from the list of viewpoints."""
    #     return {viewpoint.split("_")[0] for viewpoint in self.viewpoints}


class SimBotAuxiliaryMetadataPayload(SimBotPayload, SimBotAuxiliaryMetadata):
    """SimBot Action for the game metadata, which automatically parses it.

    When loading this class, it assumes that the auxiliary metadata file is available for parsing,
    and will error if it does not exist.
    """

    uri: SimBotAuxiliaryMetadataUri

    @classmethod
    def from_efs_uri(cls, uri: str) -> "SimBotAuxiliaryMetadataPayload":
        """Instantiate the action from just the EFS URI."""
        values_dict = cls.load_game_metadata_file(values={"uri": uri})
        return cls(**values_dict)

    @root_validator(pre=True)
    @classmethod
    def load_game_metadata_file(cls, values: dict[str, Any]) -> dict[str, Any]:  # noqa: WPS110
        """Load the game metadata from the file to fill in the remaining fields."""
        uri = values.get("uri")
        if uri is None:
            raise AssertionError("URI for the metadata file does not exist.")

        # Convert the EFS URi to a full path
        efs_uri = (
            uri
            if isinstance(uri, SimBotAuxiliaryMetadataUri)
            else SimBotAuxiliaryMetadataUri(url=str(uri), scheme="efs")
        )
        metadata_path = efs_uri.resolve_path(SimBotSettings.from_env().auxiliary_metadata_dir)

        # Load the raw metadata and update the values dict
        raw_metadata: dict[str, Any] = orjson.loads(metadata_path.read_bytes())
        values.update(raw_metadata)
        return values
