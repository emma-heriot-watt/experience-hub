from typing import Union

import httpx
from loguru import logger
from numpy.typing import ArrayLike
from PIL import Image
from pydantic import AnyHttpUrl

from emma_experience_hub.api.clients.feature_extractor import FeatureExtractorClient


class PlaceholderVisionClient(FeatureExtractorClient):
    """Run the placeholder vision client."""

    def healthcheck(self) -> bool:
        """Verify the service is healthy."""
        return self._run_healthcheck(f"{self._endpoint}/healthcheck")

    def get_object_mask_from_image(
        self, raw_utterance: str, image: Union[Image.Image, ArrayLike]
    ) -> list[list[int]]:
        """Get the object mask for the buttons."""
        image_bytes = self._convert_single_image_to_bytes(image)
        response = httpx.post(
            f"{self._endpoint}/get-button",
            params={"text": raw_utterance},
            files={self._single_image_post_arg_name: image_bytes},
        )

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception("Unable to extract mask for the button", exc_info=err)
            raise err from None

        # Process the response
        try:
            return response.json()["mask"]
        except KeyError as response_err:
            logger.error("Unable to get the mask from the response", exc_info=response_err)
            raise response_err from None
