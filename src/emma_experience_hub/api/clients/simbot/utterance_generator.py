import random
from pathlib import Path

import yaml
from convert_case import lower_case
from loguru import logger

from emma_experience_hub.api.clients.client import Client
from emma_experience_hub.datamodels.simbot import SimBotIntent, SimBotIntentType


class SimBotUtteranceGeneratorClient(Client):
    """Generate utterances for various intents."""

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
        """Generate a response from the template.

        Importantly, we use `lower_case` from `convert-case` to convert slot values to lowercase,
        so that any PascalCase or camelCase are converted properly.

        For example:
        - "MainOffice" -> "main office"
        - "pickUp" -> "pick up"
        """
        logger.debug(f"Generating utterance for intent {intent}")
        template = random.choice(self._templates[intent.type])

        return template.format(
            action=lower_case(intent.action) if intent.action else "perform that action on",
            entity=lower_case(intent.entity) if intent.entity else "object",
        )
