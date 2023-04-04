import httpx
from loguru import logger
from opentelemetry import trace
from PIL import Image

from emma_experience_hub.api.clients.feature_extractor import FeatureExtractorClient


tracer = trace.get_tracer(__name__)


class SimBotPlaceholderVisionClient(FeatureExtractorClient):
    """Run the placeholder vision client."""

    def healthcheck(self) -> bool:
        """Verify the service is healthy."""
        return self._run_healthcheck(f"{self._endpoint}/healthcheck")

    def get_embiggenator_mask(self, image: Image.Image) -> list[list[int]]:
        """Get the mask for the embiggenator."""
        image_bytes = self._convert_single_image_to_bytes(image)
        response = httpx.post(
            f"{self._endpoint}/embiggenator-mask",
            files={self._single_image_post_arg_name: image_bytes},
        )

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception("Unable to extract mask for the button")
            raise err from None

        # Process the response
        try:
            return response.json()[0]
        except KeyError as response_err:
            logger.error("Unable to get the mask from the response")
            raise response_err from None
