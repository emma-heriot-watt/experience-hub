from typing import Callable, Union

import httpx
from loguru import logger
from pydantic import AnyHttpUrl

from emma_experience_hub.api.clients.client import Client
from emma_experience_hub.datamodels.simbot import SimBotIntent, SimBotIntentType


class SimBotUtteranceGeneratorClient(Client):
    """Generate utterances for various intents."""

    def __init__(self, endpoint: AnyHttpUrl) -> None:
        self._endpoint = endpoint

    @property
    def intent_generator_switcher(
        self,
    ) -> dict[SimBotIntentType, Callable[[SimBotIntent], Union[httpx.Response, str]]]:
        """Get a dictionary of response generators for the given intent."""
        return {
            # Improper instructions
            SimBotIntentType.low_asr_confidence: self.for_low_asr_confidence,
            SimBotIntentType.profanity: self.for_profanity,
            SimBotIntentType.out_of_domain: self.for_out_of_domain,
            # Clarification questions
            SimBotIntentType.clarify_direction: self.for_clarify_direction_question,
            SimBotIntentType.clarify_description: self.for_clarify_description_question,
            SimBotIntentType.clarify_location: self.for_clarify_location_question,
            SimBotIntentType.clarify_disambiguation: self.for_clarify_disambiguation_question,
            SimBotIntentType.clarify_confirmation: self.for_clarify_confirmation_question,
            # Success feedback
            SimBotIntentType.generic_success: self.for_generic_success,
            SimBotIntentType.object_interaction_success: self.for_object_interaction_success,
            SimBotIntentType.low_level_navigation_success: self.for_low_level_navigation_success,
            SimBotIntentType.goto_room_success: self.for_goto_room_success,
            SimBotIntentType.goto_object_success: self.for_goto_object_success,
            # Failure feedback
            SimBotIntentType.generic_failure: self.for_generic_failure,
            # Feedback for arena errors
            SimBotIntentType.unsupported_action: self.for_unsupported_action,
            SimBotIntentType.unsupported_navigation: self.for_unsupported_navigation,
            SimBotIntentType.already_holding_object: self.for_already_holding_object,
            SimBotIntentType.receptacle_is_full: self.for_receptacle_is_full,
            SimBotIntentType.receptacle_is_closed: self.for_receptacle_is_closed,
            SimBotIntentType.target_inaccessible: self.for_target_inaccessible,
            SimBotIntentType.target_out_of_range: self.for_target_out_of_range,
            SimBotIntentType.object_overloaded: self.for_object_overloaded,
            SimBotIntentType.object_unpowered: self.for_object_unpowered,
            SimBotIntentType.no_free_hand: self.for_no_free_hand,
            SimBotIntentType.object_not_picked_up: self.for_object_not_picked_up,
        }

    def healthcheck(self) -> bool:
        """Verify the server is healthy."""
        response = httpx.get(f"{self._endpoint}/healthcheck")

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            logger.exception("Unable to perform healthcheck on utterance generator", exc_info=err)
            return False

        return True

    def generate_from_intent(self, intent: SimBotIntent) -> str:
        """Generate a response from the given intent."""
        generator = self.intent_generator_switcher[intent.type]

        # Generate a response
        response = generator(intent)

        # If a response is from a HTTPX request, convert it to a string
        if isinstance(response, httpx.Response):
            response = self._process_httpx_response(response)

        return response

    def for_low_asr_confidence(self, intent: SimBotIntent) -> str:
        """Generate response when the ASR confidence is too low."""
        return "Sorry, I wasn't able to understand what you said. Are you able to repeat that for me please?"

    def for_profanity(self, intent: SimBotIntent) -> httpx.Response:
        """Generate a response handling the profanity intent."""
        return httpx.post(f"{self._endpoint}/generate/profanity")

    def for_out_of_domain(self, intent: SimBotIntent) -> httpx.Response:
        """Generate a response for out of domain utterances."""
        return self.for_profanity(intent)

    def for_generic_success(self, intent: SimBotIntent) -> httpx.Response:
        """Generate a response for the `Done` intent."""
        return httpx.post(f"{self._endpoint}/generate/done")

    def for_object_interaction_success(self, intent: SimBotIntent) -> httpx.Response:
        """Generate feedback when successfully performing an action on an entity."""
        return self.for_generic_success(intent)

    def for_goto_room_success(self, intent: SimBotIntent) -> httpx.Response:
        """Generate feedback when successfully performing an action on an entity."""
        return self.for_generic_success(intent)

    def for_goto_object_success(self, intent: SimBotIntent) -> httpx.Response:
        """Generate feedback when successfully performing an action on an entity."""
        return self.for_generic_success(intent)

    def for_low_level_navigation_success(self, intent: SimBotIntent) -> str:
        """Generate a response for low level navigation success."""
        return "Okay!"

    def for_generic_failure(self, intent: SimBotIntent) -> str:
        """Generate a response when the model just fails and we are unable to determine why."""
        return "Sorry, I'm struggling with this one. Are you able to be more specific please?"

    def for_clarify_direction_question(self, intent: SimBotIntent) -> httpx.Response:
        """Generate a question to clarify the direction."""
        return httpx.post(f"{self._endpoint}/generate/clarify_direction")

    def for_clarify_description_question(self, intent: SimBotIntent) -> httpx.Response:
        """Generate a question to clarify the object description."""
        request_json = {"object": intent.entity} if intent.entity else None
        return httpx.post(
            f"{self._endpoint}/generate/clarify_object_description", json=request_json
        )

    def for_clarify_location_question(self, intent: SimBotIntent) -> httpx.Response:
        """Generate a question to clarify the object location."""
        request_json = {"object": intent.entity} if intent.entity else None
        return httpx.post(f"{self._endpoint}/generate/clarify_object_location", json=request_json)

    def for_clarify_disambiguation_question(self, intent: SimBotIntent) -> httpx.Response:
        """Generate a clarification question for object disambiguation."""
        request_json = {"object": intent.entity} if intent.entity else None
        return httpx.post(
            f"{self._endpoint}/generate/clarify_object_disambiguation", json=request_json
        )

    def for_clarify_confirmation_question(self, intent: SimBotIntent) -> str:
        """Generate a clarification question to ask confirmation."""
        raise NotImplementedError

    def for_unsupported_action(self, intent: SimBotIntent) -> str:
        """Generate feedback for unsupported_action error."""
        return self.for_generic_failure(intent)

    def for_unsupported_navigation(self, intent: SimBotIntent) -> str:
        """Generate feedback for an unsupported navigation action."""
        return self.for_generic_failure(intent)

    def for_already_holding_object(self, intent: SimBotIntent) -> str:
        """Generate feedback for the already_holding_object error."""
        entity = intent.entity or "receptacle"
        return f"I am already holding the {entity}?"

    def for_receptacle_is_full(self, intent: SimBotIntent) -> str:
        """Generate feedback for the receptacle_is_full error."""
        entity = intent.entity or "receptacle"
        return f"It looks like the {entity} is full."

    def for_receptacle_is_closed(self, intent: SimBotIntent) -> str:
        """Generate feedback for the receptacle_is_closed error."""
        entity = intent.entity or "receptacle"
        return f"Sorry, I can't do that because the {entity} is closed."

    def for_target_inaccessible(self, intent: SimBotIntent) -> str:
        """Generate feedback for the target_inaccessible error."""
        entity = intent.entity or "object"
        return f"Sorry, I can't access that {entity} currently."

    def for_target_out_of_range(self, intent: SimBotIntent) -> str:
        """Generate feedback for the target_out_of_range error."""
        entity = intent.entity or "object"
        return f"That {entity} is currently too far away. Could you help me get closer to it?"

    def for_object_overloaded(self, intent: SimBotIntent) -> str:
        """Generate feedback for the object_overloaded error."""
        return "Hmm, it seems like it is currently overloaded. I think we need to fix that first?"

    def for_object_unpowered(self, intent: SimBotIntent) -> str:
        """Generate feedback for the object_unpowered error."""
        return (
            "Hmm, it seems like it's not currently powered. I think we need to handle that first?"
        )

    def for_no_free_hand(self, intent: SimBotIntent) -> str:
        """Generate feedback for the no_free_hand error."""
        return "Sorry, I'm already holding something and I can't hold anything else. We should put down what I am holding first."

    def for_object_not_picked_up(self, intent: SimBotIntent) -> str:
        """Generate feedback for the object_not_picked_up error."""
        entity = intent.entity or "object"
        return f"Sorry, I wasn't able to pick up the {entity}."

    def _process_httpx_response(self, response: httpx.Response) -> str:
        """Process the httpx response and convert to an utterance."""
        try:
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.exception("Unable to get response from utterance generator", exc_info=err)
            raise err from None

        return response.json()
