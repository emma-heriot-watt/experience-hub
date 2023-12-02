from io import BytesIO
from typing import Union

import httpx
import numpy as np
import torch
from loguru import logger
from numpy.typing import ArrayLike
from PIL import Image

from emma_common.datamodels import TorchDataMixin
from emma_experience_hub.api.clients.client import Client
from emma_experience_hub.datamodels import EmmaExtractedFeatures


class FeatureExtractorClient(Client):
    """API Client for sending requests to the feature extractor server."""

    _single_image_post_arg_name: str = "input_file"
    _multiple_images_post_arg_name: str = "images"

    def healthcheck(self) -> bool:
        """Verify the feature extractor server is healthy."""
        return self._run_healthcheck(f"{self._endpoint}/ping")

    def change_device(self, device: torch.device) -> None:
        """Change the device used by the feature extractor.

        This is primarily useful for ensuring the perception and policy model are on the same GPU.
        """
        logger.info(f"Asking Feature Extractor to move to device: `{device}`")

        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                f"{self._endpoint}/update_model_device", json={"device": str(device)}
            )

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.warning(f"Feature extractor model not moved to device `{device}`")
            raise err

        if response.status_code == httpx.codes.OK:
            logger.info(f"Feature extractor model moved to device `{device}`")

    def process_single_image(self, image: Union[Image.Image, ArrayLike]) -> EmmaExtractedFeatures:
        """Submit a request to the feature extraction server for a single image."""
        image_bytes = self._convert_single_image_to_bytes(image)

        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                f"{self._endpoint}/features",
                files={self._single_image_post_arg_name: image_bytes},
            )

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception("Unable to extract features for a single image")
            raise err from None

        # Process the response
        feature_response = TorchDataMixin.get_object(response.content)

        return feature_response

    def process_many_images(
        self, images: Union[list[Image.Image], list[ArrayLike]]
    ) -> list[EmmaExtractedFeatures]:
        """Send a batch of images to be extracted by the server.

        There is no batch size limit for the client to send, as the server will extract the maximum
        number of images as it can at any one time.
        """
        # Build the request from the images
        all_images_as_bytes: list[bytes] = [
            self._convert_single_image_to_bytes(image) for image in images
        ]
        request_files: list[tuple[str, tuple[str, bytes]]] = [
            (self._multiple_images_post_arg_name, (str(idx), image_bytes))
            for idx, image_bytes in enumerate(all_images_as_bytes)
        ]

        # Make the request
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(f"{self._endpoint}/batch_features", files=request_files)

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception("Unable to extract features for multiple images")
            raise err from None

        # Process the response
        all_feature_responses: list[EmmaExtractedFeatures] = TorchDataMixin.get_object(
            response.content
        )

        return all_feature_responses

    def _convert_single_image_to_bytes(self, image: Union[Image.Image, ArrayLike]) -> bytes:
        """Converts a single image to bytes."""
        image_bytes = BytesIO()

        if not isinstance(image, Image.Image):
            image = Image.fromarray(np.array(image))

        image.save(image_bytes, format=image.format)
        return image_bytes.getvalue()
