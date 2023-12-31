import json
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any

import orjson

from emma_experience_hub.common.settings.simbot import SimBotRoomSearchBudget
from emma_experience_hub.datamodels.simbot.enums import SimBotActionType


constants_absolute_path = Path(__file__).parent.resolve()


@lru_cache(maxsize=1)
def get_arena_definitions() -> dict[str, Any]:
    """Load the arena definitions from their file."""
    path = constants_absolute_path.joinpath("simbot", "arena_definitions.json")
    return orjson.loads(path.read_bytes())


@lru_cache(maxsize=1)
def get_simbot_objects_to_indices_map(lowercase_keys: bool = False) -> dict[str, int]:
    """Load map of object labels to their index."""
    ignored_objects = ["Unassigned", "TAM Prototype"]

    mapping = {
        label: idx
        for label, idx in get_arena_definitions()["label_to_idx"].items()
        if label not in ignored_objects
    }

    if lowercase_keys:
        mapping = {label.lower(): idx for label, idx in mapping.items()}

    return mapping


@lru_cache(maxsize=1)
def get_simbot_object_id_to_class_name_map(lowercase_keys: bool = False) -> dict[str, str]:
    """Load map of objects from their Arena ID to the object class name."""
    mapping = get_arena_definitions()["object_id_to_class_name"]

    if lowercase_keys:
        mapping = {label.lower(): output for label, output in mapping.items()}

    return mapping


@lru_cache(maxsize=1)
def get_simbot_object_label_to_class_name_map(lowercase_keys: bool = False) -> dict[str, str]:
    """Load map of object labels to their class name."""
    mapping = get_arena_definitions()["label_to_class_name"]

    if lowercase_keys:
        mapping = {label.lower(): output for label, output in mapping.items()}

    return mapping


@lru_cache(maxsize=1)
def get_simbot_room_names(lowercase: bool = False) -> set[str]:
    """Load room name identifiers."""
    room_names = set(get_arena_definitions()["room_names"])

    if lowercase:
        room_names = {room.lower() for room in room_names}

    return room_names


@lru_cache(maxsize=1)
def get_simbot_room_name_map() -> dict[str, str]:
    """Map lowercase SimBot room names to their class name."""
    return {room_name.lower(): room_name for room_name in get_simbot_room_names()}


@lru_cache(maxsize=1)
def get_search_budget() -> dict[str, SimBotRoomSearchBudget]:
    """Load the search_budget per room from file."""
    json_path = constants_absolute_path.joinpath("simbot", "search_budget.json")
    rooms = get_simbot_room_names()
    with open(json_path) as json_file:
        search_budget = json.load(json_file)
    return {room: SimBotRoomSearchBudget(**search_budget[room]) for room in rooms}


ACTION_SYNONYMS: Mapping[SimBotActionType, set[str]] = MappingProxyType(
    {
        SimBotActionType.Goto: {"GoTo", "goto", "Goto"},
        SimBotActionType.MoveForward: {"Move Forward", "move forward"},
        SimBotActionType.MoveBackward: {"Move Backward", "move backward"},
        SimBotActionType.RotateLeft: {"Rotate Left", "rotate left"},
        SimBotActionType.RotateRight: {"Rotate Right", "rotate right"},
        SimBotActionType.LookUp: {"Look Up", "look up"},
        SimBotActionType.LookDown: {"Look Down", "look down"},
        SimBotActionType.LookAround: {"Look Around", "look around"},
        SimBotActionType.TurnAround: {"Turn Around", "turn around"},
        SimBotActionType.Pickup: {"PickUp", "pickup"},
        SimBotActionType.Open: {"Open", "open"},
        SimBotActionType.Close: {"Close", "close"},
        SimBotActionType.Break: {"Break", "break"},
        SimBotActionType.Scan: {"Scan", "scan"},
        SimBotActionType.Examine: {"Examine", "examine"},
        SimBotActionType.Place: {"Place", "place"},
        SimBotActionType.Pour: {"Pour", "pour"},
        SimBotActionType.Toggle: {"Toggle", "toggle"},
        SimBotActionType.Fill: {"Fill", "fill"},
        SimBotActionType.Clean: {"Clean", "clean"},
        SimBotActionType.Highlight: {"Highlight", "highlight"},
    }
)

_ACTION_SYNONYMS_FOR_GENERATION: Mapping[str, str] = MappingProxyType(
    {
        "GotoRoom": "go to",
        "GotoObject": "go to",
        "MoveForward": "move forward",
        "MoveBackward": "move backward",
        "RotateLeft": "rotate left",
        "RotateRight": "rotate right",
        "LookUp": "look up",
        "LookDown": "look down",
        "LookAround": "look around",
        "TurnAround": "turn around",
        "Pickup": "pick up",
        "Laser Shelf": "red shelf",
        "Laser Monitor": "red monitor",
        "Freeze Ray Shelf": "blue shelf",
        "Freeze Ray Monitor": "blue computer",
        "Gravity Monitor": "green computer",
        "Embiggenator Monitor": "pink computer",
        "Portal Generator Monitor": "black computer",
        "Everything's A Carrot Machine": "carrot machine",
        "Coffee Unmaker": "coffee composer",
    }
)

_ROOM_SYNONYNMS: Mapping[str, str] = MappingProxyType(
    {
        "BreakRoom": "breakroom",
        "Lab1": "robotics lab",
        "Lab2": "quantum lab",
        "MainOffice": "main office",
        "Reception": "reception",
        "SmallOffice": "small office",
        "Warehouse": "warehouse",
    }
)

ACTION_SYNONYMS_FOR_GENERATION: Mapping[str, str] = MappingProxyType(
    {
        **{k.lower(): v for k, v in _ACTION_SYNONYMS_FOR_GENERATION.items()},
        **_ACTION_SYNONYMS_FOR_GENERATION,
    }
)

ROOM_SYNONYNMS: Mapping[str, str] = MappingProxyType(
    {
        **{k.lower(): v for k, v in _ROOM_SYNONYNMS.items()},
        **_ROOM_SYNONYNMS,
    }
)
