from io import BytesIO
from typing import Union

import httpx
import numpy as np
import torch
from numpy.typing import ArrayLike
from PIL import Image
from pydantic import AnyHttpUrl

from emma_experience_hub.common.logging import get_logger
from emma_experience_hub.datamodels import EmmaExtractedFeatures


logger = get_logger("feature_extractor_client")


class FeatureExtractorClient:
    """API Client for sending requests to the feature extractor server."""

    def __init__(
        self,
        feature_extractor_server_endpoint: AnyHttpUrl,
        _single_image_post_arg_name: str = "input_file",
        _multiple_images_post_arg_name: str = "images",
    ) -> None:
        self._endpoint = feature_extractor_server_endpoint

        # TODO: Is there a better way to store these links?
        self._healthcheck_endpoint = f"{self._endpoint}/ping"
        self._extract_single_feature_endpoint = f"{self._endpoint}/features"
        self._extract_batch_features_endpoint = f"{self._endpoint}/batch_features"
        self._change_model_device_endpoint = f"{self._endpoint}/update_model_device"

        # TODO: These are horrendous names and need to be improved.
        self._single_image_post_arg_name = _single_image_post_arg_name
        self._multiple_images_post_arg_name = _multiple_images_post_arg_name

    def healthcheck(self) -> bool:
        """Verify the feature extractor server is healthy."""
        response = httpx.get(self._healthcheck_endpoint)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            logger.exception(err)
            return False

        return True

    def change_device(self, device: torch.device) -> None:
        """Change the device used by the feature extractor.

        This is primarily useful for ensuring the perception and policy model are on the same GPU.
        """
        logger.info(f"Asking Feature Extractor to move to device: `{device}`")

        response = httpx.post(self._change_model_device_endpoint, json={"device": str(device)})

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.warning(f"Feature extractor model not moved to device `{device}`", exc_info=err)

        if response.status_code == httpx.codes.OK:
            logger.info(f"Feature extractor model moved to device `{device}`")

    def process_single_image(self, image: Union[Image.Image, ArrayLike]) -> EmmaExtractedFeatures:
        """Submit a request to the feature extraction server for a single image."""
        image_bytes = self._convert_single_image_to_bytes(image)
        response = httpx.post(
            self._extract_single_feature_endpoint,
            files={self._single_image_post_arg_name: image_bytes},
        )

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception(err)

            # TODO: Is this the best way to handle an error here?
            raise SystemExit(err)

        # Process the response
        raw_response_data: dict[str, ArrayLike] = response.json()
        feature_response = EmmaExtractedFeatures.from_raw_response(raw_response_data)

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
        # TODO: Does the feature extractor change the order of the images?
        response = httpx.post(self._extract_batch_features_endpoint, files=request_files)

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception(err)

            # TODO: Is this the best way to handle an error here?
            raise SystemExit(err)

        # Process the response
        raw_response_data: list[dict[str, ArrayLike]] = response.json()
        all_feature_responses = list(
            map(EmmaExtractedFeatures.from_raw_response, raw_response_data)
        )
        return all_feature_responses

    def _convert_single_image_to_bytes(self, image: Union[Image.Image, ArrayLike]) -> bytes:
        """Converts a single image to bytes."""
        image_bytes = BytesIO()

        if not isinstance(image, Image.Image):
            image = Image.fromarray(np.array(image))

        image.save(image_bytes, format=image.format)
        return image_bytes.getvalue()
