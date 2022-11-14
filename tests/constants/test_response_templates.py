import itertools
import re
from pathlib import Path

import yaml
from pytest_cases import fixture

from emma_experience_hub.constants.simbot import constants_absolute_path


@fixture(scope="session")
def templates_file_path() -> Path:
    """Get the path to the response templates file."""
    return constants_absolute_path.joinpath("simbot/", "response_templates.yaml")


@fixture(scope="session")
def response_templates(templates_file_path: Path) -> dict[str, list[str]]:
    return yaml.safe_load(templates_file_path.read_text())


def test_all_templates_only_use_correct_slot_names(
    response_templates: dict[str, list[str]]
) -> None:
    # Only slot names which are allowed in a given template
    allowed_slot_names = {"entity", "action"}

    # Get every word between matching pairs of curly brackets
    template_regex = r"\{([A-Za-z0-9_]+)\}"

    templates_list = itertools.chain.from_iterable(response_templates.values())

    for template in templates_list:
        slot_names: list[str] = re.findall(template_regex, template)

        for slot_name in slot_names:
            assert slot_name in allowed_slot_names
