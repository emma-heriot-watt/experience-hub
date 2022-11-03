from typing import Optional

import httpx
from loguru import logger
from pydantic import AnyHttpUrl

from emma_experience_hub.api.clients.client import Client


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
            logger.exception("Unable to perform healthcheck on utterance generator", exc_info=err)
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

    def get_raised_exception_for_lack_of_buttons(self) -> str:
        """Generate a response when the placeholder model failed to detect buttons."""
        return (
            "Sorry, I can't see a button in front of me. Can you tell me how to move closer to it?"
        )

    def get_too_low_asr_confidence_response(self) -> str:
        """Generate response when the ASR confidence is too low."""
        return "Sorry, I wasn't able to understand what you said. Are you able to repeat that for me please?"

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

    def get_feedback_for_already_holding_object(self) -> str:
        """Generate feedback for the already_holding_object error."""
        return "I am already holding the object?"

    def get_feedback_for_receptacle_is_full(self) -> str:
        """Generate feedback for the receptacle_is_full error."""
        return "It looks like the receptacle is full."

    def get_feedback_for_receptacle_is_closed(self) -> str:
        """Generate feedback for the receptacle_is_closed error."""
        return "Sorry, I can't do that because the receptacle is closed."

    def get_feedback_for_target_inaccessible(self) -> str:
        """Generate feedback for the target_inaccessible error."""
        return "Sorry, I can't access that object currently."

    def get_feedback_for_target_out_of_range(self) -> str:
        """Generate feedback for the target_out_of_range error."""
        return "That object is currently too far away. Could you help me get closer to it?"

    def get_feedback_for_object_overloaded(self) -> str:
        """Generate feedback for the object_overloaded error."""
        return "Hmm, it seems like it is currently overloaded. I think we need to fix that first?"

    def get_feedback_for_object_unpowered(self) -> str:
        """Generate feedback for the object_unpowered error."""
        return (
            "Hmm, it seems like it's not currently powered. I think we need to handle that first?"
        )

    def get_feedback_for_no_free_hand(self) -> str:
        """Generate feedback for the no_free_hand error."""
        return "Sorry, I'm already holding something and I can't hold anything else. We should put down what I am holding first."

    def get_feedback_for_object_not_picked_up(self) -> str:
        """Generate feedback for the object_not_picked_up error."""
        return "Sorry, I wasn't able to pick up the object."

    def _send_request(self, endpoint: str, request_json: Optional[dict[str, str]] = None) -> str:
        if request_json is None:
            response = httpx.post(endpoint)
        else:
            response = httpx.post(endpoint, json=request_json)

        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception("Unable to get response from utterance generator", exc_info=err)
            raise err from None

        return response.json()
