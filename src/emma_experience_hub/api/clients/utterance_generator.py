from typing import Optional

import httpx
from pydantic import AnyHttpUrl

from emma_experience_hub.api.clients.client import Client
from emma_experience_hub.common.logging import get_logger


logger = get_logger("utterance_generator_client")


class UtteranceGeneratorClient(Client):
    """Generate utterances for various intents."""

    def __init__(self, endpoint: AnyHttpUrl) -> None:
        self._endpoint = endpoint

    def healthcheck(self) -> bool:
        """Verify the server is healthy."""
        response = httpx.get(f"{self._endpoint}/healthcheck")

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            logger.exception(err, exc_info=err)
            return False

        return True

    def get_finished_response(self) -> str:
        """Generate a response for the `Done` intent."""
        return self._send_request(f"{self._endpoint}/generate/done")

    def get_profanity_response(self) -> str:
        """Generate a response handling the profanity intent."""
        return self._send_request(f"{self._endpoint}/generate/profanity")

    def get_out_of_domain_response(self) -> str:
        """Generate a response for out of domain utterances."""
        return self.get_profanity_response()

    def get_raised_exception_response(self) -> str:
        """Generate a question asking for more help."""
        return "Sorry, I'm struggling with this one. Are you able to be more specific please?"

    def get_direction_clarify_question(self) -> str:
        """Generate clarification question for direction."""
        return self._send_request(f"{self._endpoint}/generate/clarify_direction")

    def get_object_description_clarify_question(self, object_name: Optional[str]) -> str:
        """Generate a clarification question for the object description."""
        request_json = {"object": object_name} if object_name else None
        return self._send_request(
            f"{self._endpoint}/generate/clarify_object_description", request_json
        )

    def get_object_location_clarify_question(self, object_name: Optional[str]) -> str:
        """Generate a clarification question for the object location."""
        request_json = {"object": object_name} if object_name else None
        return self._send_request(
            f"{self._endpoint}/generate/clarify_object_location", request_json
        )

    def get_object_disambiguation_clarify_question(self, object_name: Optional[str]) -> str:
        """Generate a clarification question for object disambiguation."""
        request_json = {"object": object_name} if object_name else None
        return self._send_request(
            f"{self._endpoint}/generate/clarify_object_disambiguation", request_json
        )

    def _send_request(self, endpoint: str, request_json: Optional[dict[str, str]] = None) -> str:
        if request_json is None:
            response = httpx.post(endpoint)
        else:
            response = httpx.post(endpoint, json=request_json)

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception(err, exc_info=err)
            raise err from None

        return response.json()
