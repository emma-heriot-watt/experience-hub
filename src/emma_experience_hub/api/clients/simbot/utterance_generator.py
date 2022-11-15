import random
from contextlib import suppress
from pathlib import Path
from typing import Optional

import yaml
from loguru import logger

from emma_experience_hub.api.clients.client import Client
from emma_experience_hub.constants.simbot import ACTION_SYNONYMS, ROOM_SYNONYNMS
from emma_experience_hub.datamodels.simbot import SimBotActionType, SimBotIntent, SimBotIntentType


class SimBotUtteranceGeneratorClient(Client):
    """Generate utterances for various intents."""

    _default_action = "perform that action on"
    _default_entity = "object"

    def __init__(self, templates: dict[SimBotIntentType, list[str]]) -> None:
        self._templates = templates

    @classmethod
    def from_templates_file(cls, templates_file: Path) -> "SimBotUtteranceGeneratorClient":
        """Load the templates from a yaml file."""
        raw_templates = yaml.safe_load(templates_file.read_text())

        try:
            templates = {
                SimBotIntentType[intent]: template_list
                for intent, template_list in raw_templates.items()
            }
        except Exception as err:
            logger.exception("Failed to load SimBot response templates.")
            raise err

        return cls(templates=templates)

    def healthcheck(self) -> bool:
        """It's always true since the templates are store in memory."""
        return True

    def generate_from_intent(self, intent: SimBotIntent) -> str:
        """Generate a response from the template."""
        logger.debug(f"Generating utterance for intent {intent}")
        template = random.choice(self._templates[intent.type])

        return template.format(
            action=self._get_action_name(intent.action),
            entity=self._get_entity_name(intent.entity),
        )

    def _get_action_name(self, action_type: Optional[SimBotActionType]) -> str:
        """Return one of the synonyms for the action type."""
        if not action_type:
            return self._default_action

        with suppress(KeyError):
            return random.choice(list(ACTION_SYNONYMS[action_type]))

        return self._default_action

    def _get_entity_name(self, entity: Optional[str]) -> str:
        """Return a synonym for the entity name if possible."""
        if not entity:
            return self._default_entity

        with suppress(KeyError):
            return ROOM_SYNONYNMS[entity]

        # Return itself if there were no synonyms for it
        return entity
