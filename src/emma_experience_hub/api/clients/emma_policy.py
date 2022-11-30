from typing import Any

import httpx
import orjson
from loguru import logger
from pydantic import AnyHttpUrl

from emma_experience_hub.datamodels import (
    DialogueUtterance,
    EmmaPolicyRequest,
    EnvironmentStateTurn,
)


class EmmaPolicyClient:
    """API client for interfacing with an EMMA Policy model."""

    def __init__(self, server_endpoint: AnyHttpUrl) -> None:
        self._endpoint = server_endpoint

    def healthcheck(self) -> bool:
        """Verify the server is online and healthy."""
        response = httpx.get(f"{self._endpoint}/ping")

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            logger.exception("Unable to perform healtcheck on EMMA policy server", exc_info=err)
            return False

        return True

    def generate(
        self,
        environment_state_history: list[EnvironmentStateTurn],
        dialogue_history: list[DialogueUtterance],
    ) -> str:
        """Generate a response from the features and provided language."""
        return self._make_request(
            f"{self._endpoint}/generate", environment_state_history, dialogue_history
        )

    def _make_request(
        self,
        endpoint: str,
        environment_state_history: list[EnvironmentStateTurn],
        dialogue_history: list[DialogueUtterance],
    ) -> Any:
        """Generate a response from the features and provided language."""
        emma_policy_request = EmmaPolicyRequest(
            environment_history=environment_state_history, dialogue_history=dialogue_history
        )
        logger.debug(f"Sending {emma_policy_request.num_images} images.")

        logger.debug(f"Sending dialogue history: {emma_policy_request.dialogue_history}")

        response = httpx.post(
            endpoint,
            json=orjson.loads(
                emma_policy_request.json(
                    models_as_dict=True,
                    exclude={
                        "environment_history": {
                            "__all__": {"features": {"__all__": {"class_labels"}}}
                        }
                    },
                )
            ),
        )

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception("Unable to get response from EMMA policy server", exc_info=err)
            raise err from None

        json_response = response.json()
        logger.debug(f"Response from policy endpoint `{endpoint}`: {json_response}")
        return json_response
