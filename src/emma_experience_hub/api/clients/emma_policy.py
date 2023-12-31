from typing import Any, Optional

import httpx
from loguru import logger

from emma_common.datamodels import (
    DialogueUtterance,
    EmmaPolicyRequest,
    EnvironmentStateTurn,
    TorchDataMixin,
)
from emma_experience_hub.api.clients.client import Client


class EmmaPolicyClient(Client):
    """API client for interfacing with an EMMA Policy model."""

    def healthcheck(self) -> bool:
        """Verify the server is online and healthy."""
        return self._run_healthcheck(f"{self._endpoint}/ping")

    def generate(
        self,
        environment_state_history: list[EnvironmentStateTurn],
        dialogue_history: list[DialogueUtterance],
    ) -> str:
        """Generate a response from the features and provided language."""
        raise NotImplementedError

    def _make_request(
        self,
        endpoint: str,
        environment_state_history: list[EnvironmentStateTurn],
        dialogue_history: list[DialogueUtterance],
        inventory_entity: Optional[str] = None,
        force_stop_token: bool = False,
    ) -> Any:
        """Generate a response from the features and provided language."""
        emma_policy_request = EmmaPolicyRequest(
            environment_history=environment_state_history,
            dialogue_history=dialogue_history,
            force_stop_token=force_stop_token,
        )
        logger.debug(f"Sending {emma_policy_request.num_images} images.")
        logger.debug(f"Sending dialogue history: {emma_policy_request.dialogue_history}")
        logger.debug(f"size of the history {len(environment_state_history)}")

        with httpx.Client(timeout=None) as client:
            response = client.post(endpoint, content=TorchDataMixin.to_bytes(emma_policy_request))

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception("Unable to get response from EMMA policy server")
            raise err from None

        json_response = response.json()
        logger.debug(f"Response from policy endpoint `{endpoint}`: {json_response}")
        return json_response
