"""Clients which handle caching data and objects for SimBot.

This class primarily has a bunch of generics which include methods to make data handling as simple
and straightforward as possible.

There are both Pydantic and non-Pydantic base classes so that clients can be composed to handle any data.

The main classes that should be used are the ones at the bottom of this module. All the generics
are just there for keep things separated and clear.
"""

from io import BytesIO
from pathlib import Path
from typing import Generic, Optional, TypeVar, Union

import boto3
import torch
from botocore.exceptions import ClientError

from emma_experience_hub.api.clients.pydantic import PydanticClient, PydanticT
from emma_experience_hub.common import get_logger
from emma_experience_hub.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.simbot.actions.auxiliary_metadata import (
    SimBotAuxiliaryMetadata,
)


log = get_logger("simbot_api_clients")

T = TypeVar("T")


class SimBotCacheClient(Generic[T]):
    """Base client for interfacing with the SimBot cache stores."""

    def check_exist(self, session_id: str, prediction_request_id: str) -> bool:
        """Check whether or not it exists."""
        raise NotImplementedError

    def save(self, data: T, session_id: str, prediction_request_id: str) -> None:
        """Store the data."""
        raise NotImplementedError

    def load(self, session_id: str, prediction_request_id: str) -> T:
        """Load the data."""
        raise NotImplementedError


class SimBotFileSystemClient(SimBotCacheClient[T]):
    """Base client for caching SimBot data on the file system.

    The `suffix` class variable must be instantiated by any subclasses.
    """

    suffix: str

    def __init__(self, root_directory: Path) -> None:
        # Ensure the root directory exists
        root_directory.mkdir(parents=True, exist_ok=True)

        self.root = root_directory

    def check_exist(self, session_id: str, prediction_request_id: str) -> bool:
        """Check whether or not the file exists."""
        return self._create_path(session_id, prediction_request_id).exists()

    def _create_path(self, session_id: str, prediction_request_id: str) -> Path:
        """Create the path for sourcing the data."""
        path = self.root.joinpath(session_id, str(prediction_request_id)).with_suffix(self.suffix)
        return path


class SimBotS3Client(SimBotCacheClient[T]):
    """Base client for caching SimBot data on S3.

    The `suffix` class variable must be instantiated by any subclasses.
    """

    suffix: str

    def __init__(self, bucket_name: str, object_prefix: Optional[str] = None) -> None:
        self.bucket = bucket_name
        self.prefix = object_prefix if object_prefix is not None else ""

    def check_exist(self, session_id: str, prediction_request_id: str) -> bool:
        """Check whether the object already exists on S3."""
        object_key = self._build_object_name(session_id, prediction_request_id)

        s3 = boto3.client("s3")
        try:
            s3.head_object(Bucket=self.bucket, Key=object_key)
        except ClientError:
            return False

        return True

    def _download(self, object_key: str) -> bytes:
        """Download a file object from S3, directly into the memory."""
        # Create the buffer that will store the bytes
        data_buffer = BytesIO()

        # Download data into the buffer.
        s3 = boto3.client("s3")
        try:
            s3.download_fileobj(Bucket=self.bucket, Key=object_key, Fileobj=data_buffer)
        except ClientError as err:
            log.exception("Failed to download object from S3", exc_info=err)

        # Return the bytes
        return data_buffer.getvalue()

    def _upload(self, data: bytes, object_key: str) -> None:
        """Upload a file object to S3, directly from the memory.

        Onus for handling exceptions should be on the users of this class.
        """
        s3 = boto3.client("s3")

        try:
            s3.upload_fileobj(Fileobj=data, Bucket=self.bucket, Key=object_key)
        except ClientError as err:
            log.exception("Failed to upload object from S3", exc_info=err)

    def _build_object_name(self, session_id: str, prediction_request_id: str) -> str:
        """Build the name of the object, including the default prefix."""
        return "/".join([self.prefix, session_id, f"{str(prediction_request_id)}.{self.suffix}"])


class SimBotPydanticFileSystemClient(SimBotFileSystemClient[PydanticT], PydanticClient[PydanticT]):
    """Cache Pydantic models for SimBot on the file system.

    Subclasses MUST have included the class variables: `suffix` and `model`.
    """

    def save(
        self, data: Union[PydanticT, bytes], session_id: str, prediction_request_id: str
    ) -> None:
        """Save the data to the file system."""
        if not isinstance(data, bytes):
            data = self._pydantic_to_bytes(data)

        destination_path = self._create_path(session_id, prediction_request_id)
        destination_path.write_bytes(data)

    def load(self, session_id: str, prediction_request_id: str) -> PydanticT:
        """Load the data from the file system."""
        path = self._create_path(session_id, prediction_request_id)
        data_as_bytes = path.read_bytes()
        parsed_model = self._pydantic_from_bytes(data_as_bytes)
        return parsed_model


class SimBotPydanticS3Client(SimBotS3Client[PydanticT], PydanticClient[PydanticT]):
    """Cache Pydantic models for SimBot on S3.

    Subclasses MUST have included the class variables: `suffix` and `model`.
    """

    def __init__(
        self,
        bucket_name: str,
        object_prefix: Optional[str] = None,
        local_backup_root_path: Optional[Path] = None,
    ) -> None:
        super().__init__(bucket_name, object_prefix)

        if local_backup_root_path is not None:
            self._local_backup = SimBotPydanticFileSystemClient[PydanticT](local_backup_root_path)

    @property
    def local_backup_client(self) -> Optional[SimBotPydanticFileSystemClient[PydanticT]]:
        """Get the client for saving the data locally too."""
        try:
            return self._local_backup
        except UnboundLocalError:
            return None

    def check_exist(self, session_id: str, prediction_request_id: str) -> bool:
        """Check if the data exists.

        Return True if it exists on S3 or locally (if local backup is enabled).
        """
        data_exists_on_s3 = super().check_exist(session_id, prediction_request_id)

        data_exists_locally: bool = False
        if self.local_backup_client is not None:
            data_exists_locally = self.local_backup_client.check_exist(
                session_id, prediction_request_id
            )

        return data_exists_on_s3 or data_exists_locally

    def save(self, data: PydanticT, session_id: str, prediction_request_id: str) -> None:
        """Save the data to S3."""
        data_bytes = self._pydantic_to_bytes(data)
        object_key = self._build_object_name(session_id, prediction_request_id)
        self._upload(data=data_bytes, object_key=object_key)

        if self.local_backup_client is not None:
            self.local_backup_client.save(data, session_id, prediction_request_id)

    def load(self, session_id: str, prediction_request_id: str) -> PydanticT:
        """Load data from S3."""
        # Check if the data exists locally first because that will e faster
        if self.local_backup_client is not None:
            if self.local_backup_client.check_exist(session_id, prediction_request_id):
                return self.local_backup_client.load(session_id, prediction_request_id)

        # if it doesn't exist locally, download from S3
        object_key = self._build_object_name(session_id, prediction_request_id)
        data_as_bytes = self._download(object_key)
        parsed_file = self._pydantic_from_bytes(data_as_bytes)

        # If it doesn't exist locally, save it locally
        if self.local_backup_client is not None:
            if not self.local_backup_client.check_exist(session_id, prediction_request_id):
                self.local_backup_client.save(data_as_bytes, session_id, prediction_request_id)

        return parsed_file


class SimBotAuxiliaryMetadataS3Client(SimBotPydanticS3Client[SimBotAuxiliaryMetadata]):
    """Cache auxiliary metadata on S3."""

    model = SimBotAuxiliaryMetadata
    suffix = "json"


class SimBotExtractedFeaturesFileSystemClient(SimBotFileSystemClient[list[EmmaExtractedFeatures]]):
    """Cache extracted features on the File system."""

    suffix = "pt"

    def save(
        self, data: list[EmmaExtractedFeatures], session_id: str, prediction_request_id: str
    ) -> None:
        """Save the extracted features to a single file.

        Convert the features into a dictioanry to serialize it into a single object.
        """
        data_as_dict = {idx: instance.dict() for idx, instance in enumerate(data)}
        path = self._create_path(session_id, prediction_request_id)
        torch.save(data_as_dict, path)

    def load(self, session_id: str, prediction_request_id: str) -> list[EmmaExtractedFeatures]:
        """Load the extracted features from a single file."""
        path = self._create_path(session_id, prediction_request_id)

        # Load the raw data from the path using torch.
        raw_data: dict[int, dict[str, torch.Tensor]] = torch.load(path)

        # Sort the raw data by key to ensure the list is built in the correct order.
        sorted_raw_data = sorted(raw_data.items())

        # Parse all the features back into the datamodels
        parsed_data = [
            EmmaExtractedFeatures.parse_obj(raw_feature_dict)
            for _, raw_feature_dict in sorted_raw_data
        ]

        return parsed_data
