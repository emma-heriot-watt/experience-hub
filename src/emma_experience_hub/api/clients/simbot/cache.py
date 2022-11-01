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

import torch
from botocore.exceptions import ClientError
from cloudpathlib import S3Client, S3Path
from loguru import logger

from emma_experience_hub.api.clients.client import Client
from emma_experience_hub.api.clients.pydantic import PydanticClientMixin, PydanticT
from emma_experience_hub.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.simbot.payloads import SimBotAuxiliaryMetadataPayload


T = TypeVar("T")


class SimBotCacheClient(Client, Generic[T]):
    """Cache client for SimBot data.

    All data is automatially cached on S3.
    """

    suffix: str

    def __init__(
        self,
        bucket_name: str,
        object_prefix: Optional[str] = None,
        local_cache_dir: Optional[Path] = None,
    ) -> None:
        self.bucket = bucket_name
        self.prefix = object_prefix if object_prefix is not None else ""

        self._s3 = S3Client(local_cache_dir=local_cache_dir)

    def healthcheck(self) -> bool:
        """Verify that the S3 bucket is available and accessible."""
        try:
            self._s3.client.head_bucket(Bucket=self.bucket)
        except ClientError as err:
            logger.exception("Failed to get S3 bucket", exc_info=err)
            return False

        return True

    def check_exist(self, session_id: str, prediction_request_id: str) -> bool:
        """Check whether or not the file exists."""
        return self._create_path(session_id, prediction_request_id).exists()

    def save(self, data: T, session_id: str, prediction_request_id: str) -> None:
        """Save the data, converting from the object to bytes."""
        raise NotImplementedError()

    def load(self, session_id: str, prediction_request_id: str) -> T:
        """Load the data, converting from bytes to the object."""
        raise NotImplementedError()

    def _save_bytes(self, data: bytes, session_id: str, prediction_request_id: str) -> None:
        """Save the data."""
        destination_path = self._create_path(session_id, prediction_request_id)
        destination_path.write_bytes(data)

    def _load_bytes(self, session_id: str, prediction_request_id: str) -> bytes:
        """Load the data."""
        path = self._create_path(session_id, prediction_request_id)
        return path.read_bytes()

    def _create_path(self, session_id: str, prediction_request_id: str) -> S3Path:
        """Build the name of the object, including the default prefix."""
        object_name = "/".join(
            [self.prefix, session_id, f"{str(prediction_request_id)}.{self.suffix}"]
        ).lstrip("/")

        return self._s3.CloudPath(f"s3://{self.bucket}/{object_name}")


class SimBotPydanticCacheClient(PydanticClientMixin[PydanticT], SimBotCacheClient[PydanticT]):
    """Cache Pydantic models for SimBot.

    Subclasses MUST have included the class variables: `suffix` and `model`.
    """

    model: type[PydanticT]
    suffix: str

    def save(
        self, data: Union[PydanticT, bytes], session_id: str, prediction_request_id: str
    ) -> None:
        """Save the data to the file system."""
        if not isinstance(data, bytes):
            data = self._pydantic_to_bytes(data)

        return self._save_bytes(data, session_id, prediction_request_id)

    def load(self, session_id: str, prediction_request_id: str) -> PydanticT:
        """Load the data from the file system."""
        data_as_bytes = self._load_bytes(session_id, prediction_request_id)
        parsed_model = self._pydantic_from_bytes(data_as_bytes)
        return parsed_model


class SimBotAuxiliaryMetadataClient(SimBotPydanticCacheClient[SimBotAuxiliaryMetadataPayload]):
    """Cache auxiliary metadata on S3."""

    model = SimBotAuxiliaryMetadataPayload
    suffix = "json"


class SimBotExtractedFeaturesClient(SimBotCacheClient[list[EmmaExtractedFeatures]]):
    """Cache extracted features on the File system."""

    suffix = "pt"

    def save(
        self, data: list[EmmaExtractedFeatures], session_id: str, prediction_request_id: str
    ) -> None:
        """Save the extracted features to a single file.

        Convert the features into a dictioanry to serialize it into a single object.
        """
        # Prepare the data
        data_as_dict = {idx: instance.dict() for idx, instance in enumerate(data)}

        # Save with torch
        data_buffer = BytesIO()
        torch.save(data_as_dict, data_buffer)

        # Write data
        self._save_bytes(data_buffer.getvalue(), session_id, prediction_request_id)

    def load(self, session_id: str, prediction_request_id: str) -> list[EmmaExtractedFeatures]:
        """Load the extracted features from a single file."""
        # Load the raw data using torch.
        raw_data: dict[int, dict[str, torch.Tensor]] = torch.load(
            BytesIO(self._load_bytes(session_id, prediction_request_id))
        )

        # Sort the raw data by key to ensure the list is built in the correct order.
        sorted_raw_data = sorted(raw_data.items())

        # Parse all the features back into the datamodels
        parsed_data = [
            EmmaExtractedFeatures.parse_obj(raw_feature_dict)
            for _, raw_feature_dict in sorted_raw_data
        ]

        return parsed_data
