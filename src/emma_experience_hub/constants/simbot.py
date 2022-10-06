from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any

import orjson

from emma_experience_hub.datamodels.simbot.actions import SimBotActionType


constants_absolute_path = Path(__file__).parent.resolve()


@lru_cache(maxsize=1)
def load_arena_definitions() -> dict[str, Any]:
    """Load the arena definitions from their file."""
    path = constants_absolute_path.joinpath("simbot", "arena_definitions.json")
    return orjson.loads(path.read_bytes())


@lru_cache(maxsize=1)
def load_simbot_objects_to_indices_map() -> dict[str, int]:
    """Load map of object labels to their index."""
    ignored_objects = ["Unassigned", "TAM Prototype"]

    return {
        label: idx
        for label, idx in load_arena_definitions()["label_to_idx"].items()
        if label not in ignored_objects
    }


@lru_cache(maxsize=1)
def load_simbot_object_id_to_class_name_map() -> dict[str, str]:
    """Load map of objects from their Arena ID to the object class name."""
    return load_arena_definitions()["object_id_to_class_name"]


@lru_cache(maxsize=1)
def load_simbot_object_label_to_class_name_map() -> dict[str, str]:
    """Load map of object labels to their class name."""
    return load_arena_definitions()["label_to_class_name"]


@lru_cache(maxsize=1)
def load_simbot_room_names() -> set[str]:
    """Load room name identifiers."""
    return set(load_arena_definitions()["room_names"])


ACTION_SYNONYMS: Mapping[SimBotActionType, set[str]] = MappingProxyType(
    {
        SimBotActionType.Goto: {"GoTo", "goto"},
        SimBotActionType.MoveForward: {"Move Forward", "move forward"},
        SimBotActionType.MoveBackward: {"Move Backward", "move backward"},
        SimBotActionType.RotateLeft: {"Rotate Left", "rotate left"},
        SimBotActionType.RotateRight: {"Rotate Right", "rotate right"},
        SimBotActionType.LookUp: {"Look Up", "look up"},
        SimBotActionType.LookDown: {"Look Down", "look down"},
        SimBotActionType.LookAround: {"Look Around", "look around"},
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
    }
)
