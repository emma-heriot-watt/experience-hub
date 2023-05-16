from typing import Optional

from pydantic import BaseModel, Field

from emma_experience_hub.constants.simbot import get_prior_memory, get_prior_memory_candidates
from emma_experience_hub.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.common import ArenaLocation, Position, RotationQuaternion
from emma_experience_hub.datamodels.simbot.actions import SimBotAction
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotObjectInteractionPayload,
    SimBotObjectMaskType,
)


class SimBotMemoryEntity(BaseModel):
    """A memory entity."""

    viewpoint: str
    area: float
    location: ArenaLocation
    interaction_turn: int = -1


SimBotRoomMemoryType = dict[str, SimBotMemoryEntity]


def get_area_from_compressed_mask(mask: SimBotObjectMaskType) -> float:
    """Compute the area of a compressed mask."""
    if not mask:
        return 0
    return sum([offset for _, offset in mask])


class SimBotObjectMemory(BaseModel):
    """Track all the observed objects and their closest viewpoints."""

    memory: dict[str, SimBotRoomMemoryType] = {}
    _prior_memory: dict[str, str] = get_prior_memory()
    _prior_memory_candidates: dict[str, list[str]] = get_prior_memory_candidates()

    def update_from_action(  # noqa: WPS231
        self,
        room_name: str,
        position: Position,
        rotation: RotationQuaternion,
        viewpoint: str,
        action: SimBotAction,
        action_history: list[SimBotAction],
        inventory_history: list[Optional[str]],
        inventory_entity: Optional[str] = None,
    ) -> None:
        """Update the memory after action execution."""
        if not action.is_successful:
            return

        # if the action removed something from the inventory then we can find in the environment
        if action.removes_object_from_inventory and inventory_entity is not None:
            self.write_inventory_entity_in_room(
                room_name=room_name,
                position=position,
                rotation=rotation,
                viewpoint=viewpoint,
                action=action,
                inventory_entity=inventory_entity,
            )

        # if the action added something to the inventory then we can't find in the environment.
        if action.adds_object_to_inventory and action.payload.entity_name is not None:
            self.memory[room_name].pop(action.payload.entity_name.lower(), None)
        # if the action transformed the object type then we can't find in the environment.
        if action.transforms_object and action.payload.entity_name is not None and action_history:
            machine = action.payload.entity_name.lower()
            # Go through past actions starting from the most recent one.
            for past_action, past_inventory in zip(action_history[::-1], inventory_history[::-1]):
                # Does the past action place the object on the machine?
                should_update_memory = self._action_places_object_to_transform(
                    past_action=past_action, machine=machine, past_inventory=past_inventory
                )

                if should_update_memory:
                    self.memory[room_name].pop(past_inventory, None)  # type: ignore[arg-type]
                    break
                # Does the past action transform the object?
                previous_interaction = (
                    past_action.transforms_object
                    and past_action.payload.entity_name is not None
                    and past_action.payload.entity_name.lower() == machine
                )
                if previous_interaction:
                    break

    def update_interaction_turn_index(
        self,
        room_name: str,
        action: SimBotAction,
        turn_index: int,
    ) -> None:
        """Update the interaction turn."""
        if not action.is_successful:
            return

        should_update_interaction_turn = (
            action.is_object_interaction
            and action.payload.entity_name is not None
            and room_name in self.memory
            and action.payload.entity_name.lower() in self.memory[room_name]
        )
        if should_update_interaction_turn:
            object_label = action.payload.entity_name.lower()  # type: ignore[union-attr]
            self.memory[room_name][object_label].interaction_turn = turn_index

    def read_memory_entity_in_room(
        self, room_name: str, object_label: str
    ) -> Optional[ArenaLocation]:
        """Read an object closest position from memory."""
        memory_room = self.memory.get(room_name, None)
        if memory_room is None:
            return None

        memory_entity = memory_room.get(object_label.lower(), None)
        if memory_entity is None:
            return None

        return memory_entity.location

    def read_memory_entity_in_arena(self, object_label: str) -> list[tuple[str, ArenaLocation]]:
        """Find all objects in memory matching the object_label."""
        found_object_locations = []
        for room in self.memory:
            memory_location = self.read_memory_entity_in_room(room, object_label)
            if memory_location is not None:
                found_object_locations.append((room, memory_location))
        return found_object_locations

    def read_prior_memory_entity_in_arena(self, object_label: str) -> Optional[str]:
        """Find object room based on prior memory."""
        return self._prior_memory.get(object_label.lower(), None)

    def object_in_memory(self, object_label: str, current_room: str) -> bool:
        """Is the object in the current room or prior memory?"""
        if self.read_memory_entity_in_room(room_name=current_room, object_label=object_label):
            return True
        object_label = object_label.lower()

        if object_label in self._prior_memory_candidates:
            return True

        return self._prior_memory.get(object_label, None) is not None

    def get_other_interacted_room(self, object_label: str) -> Optional[str]:
        """Get the room where the object was interacted with."""
        # Check if the object has multiple prior memory room candidates.
        object_label = object_label.lower()
        prior_room_candidates = self._prior_memory_candidates.get(object_label, None)
        if prior_room_candidates is None:
            return None

        # Find the most recent room where the object was interacted with.
        object_memory_entry = [
            self.memory[room].get(object_label) if room in self.memory else None
            for room in prior_room_candidates
        ]
        interaction_turns = [
            entry.interaction_turn if entry else -1 for entry in object_memory_entry
        ]
        most_recent_interaction_turn = max(interaction_turns)
        if most_recent_interaction_turn < 0:
            return None
        return prior_room_candidates[interaction_turns.index(most_recent_interaction_turn)]

    def get_entity_room_candidate(self, object_label: str) -> Optional[list[str]]:
        """Get all candidate rooms based on prior memory."""
        object_label = object_label.lower()
        prior_memory_room = self._prior_memory.get(object_label, None)
        if prior_memory_room is not None:
            return [prior_memory_room]

        return self._prior_memory_candidates.get(object_label, None)

    def write_memory_entities_in_room(
        self,
        room_name: str,
        position: Position,
        rotation: RotationQuaternion,
        viewpoint: str,
        extracted_features: list[EmmaExtractedFeatures],
    ) -> None:
        """Write new object entities in memory."""
        for frame_features in extracted_features:
            self._write_frame_entities(
                room_name=room_name,
                position=position,
                rotation=rotation,
                viewpoint=viewpoint,
                frame_features=frame_features,
            )

    def write_inventory_entity_in_room(
        self,
        room_name: str,
        position: Position,
        rotation: RotationQuaternion,
        viewpoint: str,
        action: SimBotAction,
        inventory_entity: str,
    ) -> None:
        """Write the new inventory object entity in memory."""
        if not isinstance(action.payload, SimBotObjectInteractionPayload):
            return
        if not action.payload.object.mask:
            return

        self._write(
            room_name=room_name,
            position=position,
            rotation=rotation,
            viewpoint=viewpoint,
            object_label=inventory_entity,
            area=get_area_from_compressed_mask(action.payload.object.mask),
        )

    def _write_frame_entities(
        self,
        room_name: str,
        position: Position,
        rotation: RotationQuaternion,
        viewpoint: str,
        frame_features: EmmaExtractedFeatures,
    ) -> None:
        object_labels = frame_features.entity_labels
        bbox_areas = frame_features.bbox_areas.tolist()

        if not object_labels:
            raise AssertionError("Frame features does not have entity labels")

        for object_label, object_area in zip(object_labels, bbox_areas):
            memory_room = self.memory.get(room_name, None)
            # This is the first time an entity is written in memory for that room
            if memory_room is None:
                self.memory[room_name] = {}

            self._write(
                room_name=room_name,
                position=position,
                rotation=rotation,
                viewpoint=viewpoint,
                object_label=object_label,
                area=object_area,
            )

    def _write(
        self,
        room_name: str,
        position: Position,
        rotation: RotationQuaternion,
        viewpoint: str,
        object_label: str,
        area: float,
    ) -> None:
        object_label = object_label.lower()
        memory_entity = self.memory[room_name].get(object_label, None)
        interaction_turn = memory_entity.interaction_turn if memory_entity else -1
        if memory_entity is None or memory_entity.area < area:
            location = ArenaLocation(room_name=room_name, position=position, rotation=rotation)
            self.memory[room_name][object_label] = SimBotMemoryEntity(
                viewpoint=viewpoint,
                area=area,
                location=location,
                interaction_turn=interaction_turn,
            )

    def _action_places_object_to_transform(
        self, past_action: SimBotAction, machine: str, past_inventory: Optional[str]
    ) -> bool:
        """Return True if the memory should be updated based on a past place action.

        If the past action successfuly places an object on a machine that can transform it.
        """
        action_places_object_on_machine = (
            past_action.removes_object_from_inventory
            and past_action.payload.entity_name is not None
            and past_action.payload.entity_name.lower() == machine
            and past_action.is_successful
        )
        if not action_places_object_on_machine:
            return False

        if past_action.interacts_with_time_machine:
            return past_inventory == "carrot"
        return True


class SimBotInventory(BaseModel, validate_assignment=True):
    """Track what is in the inventory of the SimBot agent.

    The turn_idx and action_id inform when the inventory were last updated.
    """

    entity: Optional[str] = None
    turn_idx: int = Field(default=0, ge=0, description="When the inventory was last updated.")

    @property
    def is_empty(self) -> bool:
        """Return True if the agent inventory is empty."""
        return not bool(self.entity)

    @classmethod
    def from_action(
        cls, action: SimBotAction, turn_idx: int, previous_inventory: Optional[str]
    ) -> "SimBotInventory":
        """Instantiate an inventory from the action."""
        if action.adds_object_to_inventory and action.is_successful:
            entity_name = action.payload.entity_name
            if entity_name is not None:
                entity_name = entity_name.lower()
            return cls(entity=entity_name, turn_idx=turn_idx)

        if action.removes_object_from_inventory and action.is_successful:
            return cls(entity=None, turn_idx=turn_idx)

        if action.is_pour and previous_inventory == "coffee beans" and action.is_successful:
            return cls(entity=None, turn_idx=turn_idx)

        raise AssertionError("Action does not alter/change the inventory in any way")
