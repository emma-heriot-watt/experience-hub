import json
from typing import Optional

import httpx
from loguru import logger
from methodtools import lru_cache
from opentelemetry import trace
from pydantic import BaseModel

from emma_experience_hub.api.clients import Client
from emma_experience_hub.datamodels.simbot.actions import SimBotAction


tracer = trace.get_tracer(__name__)

LRU_CACHE_MAX_SIZE = 64


class SimBotHacksRoom(BaseModel):
    """SimBotHack room response."""

    room_name: str
    arena_room: str
    modified_utterance: str


class SimBotHacksAnticipator(BaseModel):
    """SimBotHackAnticipator response."""

    intent: str
    utterances: list[str]


class SimBotHacksClient(Client):
    """Client to access the SimBot Hacks service."""

    def healthcheck(self) -> bool:
        """Verify the server is healthy."""
        return self._run_healthcheck(f"{self._endpoint}/healthcheck")

    def get_low_level_prediction_from_raw_text(self, utterance: str) -> Optional[str]:
        """Generate a response from the provided language."""
        with tracer.start_as_current_span("Match text to template"):
            response = self._get_low_level_prediction_from_raw_text(utterance)

        logger.debug(f"Cache info: {self._get_low_level_prediction_from_raw_text.cache_info()}")
        return response

    def get_room_prediction_from_raw_text(self, utterance: str) -> Optional[SimBotHacksRoom]:
        """Generate a room prediction from the provided language."""
        with tracer.start_as_current_span("Get room from raw text"):
            response = self._get_room_prediction_from_raw_text(utterance)

        logger.debug(f"Cache info: {self._get_room_prediction_from_raw_text.cache_info()}")
        return response

    def get_anticipator_prediction_from_action(
        self,
        action: SimBotAction,
        inventory_entity: Optional[str] = None,
    ) -> Optional[SimBotHacksAnticipator]:
        """Generate possible plan of instructions from the given action."""
        with tracer.start_as_current_span("Get anticipator plan"):
            response = self._get_anticipated_instructions(action, inventory_entity)

        logger.debug(f"Cache info: {self._get_room_prediction_from_raw_text.cache_info()}")
        return response

    @lru_cache(maxsize=LRU_CACHE_MAX_SIZE)  # noqa: B019
    def _get_low_level_prediction_from_raw_text(self, utterance: str) -> Optional[str]:
        """Generate a response from the provided language."""
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                f"{self._endpoint}/generate_raw_text_match", json={"text": utterance}
            )

        try:
            response.raise_for_status()
        except httpx.HTTPError:
            logger.warning("Unable to get an action from the raw text.")
            return None

        return response.json()

    @lru_cache(maxsize=LRU_CACHE_MAX_SIZE)  # noqa: B019
    def _get_room_prediction_from_raw_text(self, utterance: str) -> Optional[SimBotHacksRoom]:
        """Generate a room name referenced in the utterance."""
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                f"{self._endpoint}/generate_room_match", json={"text": utterance}
            )

        try:
            response.raise_for_status()
        except httpx.HTTPError:
            logger.warning("Unable to get a room from the raw text.")
            return None

        try:
            room = SimBotHacksRoom.parse_obj(response.json())
        except Exception:
            return None
        return room

    def _get_anticipated_instructions(
        self,
        action: SimBotAction,
        inventory_entity: Optional[str] = None,
    ) -> Optional[SimBotHacksAnticipator]:
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                f"{self._endpoint}/generate_anticipated_actions",
                json={
                    "simbot_action": json.loads(action.json()),
                    "holding_object": inventory_entity,
                },
            )

        try:
            response.raise_for_status()
        except httpx.HTTPError:
            logger.warning("Unable to get action plan.")
            return None

        response_json = response.json()
        if response_json is None:
            return None

        try:
            anticipator_plan = SimBotHacksAnticipator.parse_obj(response.json())
        except Exception:
            logger.exception("Unable to parse the anticipator plan")
            return None
        return anticipator_plan
