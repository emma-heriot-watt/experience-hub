from typing import Optional

from pydantic import BaseModel, Field

from emma_experience_hub.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.simbot.actions import SimBotAction
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotObjectInteractionPayload,
    SimBotObjectMaskType,
)


class SimBotMemoryEntity(BaseModel):
    """A memory entity."""

    viewpoint: str
    area: float


SimBotRoomMemoryType = dict[str, SimBotMemoryEntity]


def get_area_from_compressed_mask(mask: SimBotObjectMaskType) -> float:
    """Compute the area of a compressed mask."""
    if not mask:
        return 0
    return sum([offset for _, offset in mask])


class SimBotObjectMemory(BaseModel):
    """Track all the observed objects and their closest viewpoints."""

    memory: dict[str, SimBotRoomMemoryType] = {}

    def update_from_action(
        self,
        room_name: str,
        viewpoint: str,
        action: SimBotAction,
        inventory_entity: Optional[str] = None,
    ) -> None:
        """Update the memory after action execution."""
        if not action.is_successful:
            return
        # if the action removed something from the inventory then we can find in the environment
        if action.removes_object_from_inventory and inventory_entity is not None:
            self.write_inventory_entity_in_room(
                room_name=room_name,
                viewpoint=viewpoint,
                action=action,
                inventory_entity=inventory_entity,
            )

        # if the action added something to the inventory then we cant find in the environment.
        if action.adds_object_to_inventory and action.payload.entity_name is not None:
            self.memory[room_name].pop(action.payload.entity_name, None)

    def read_memory_entity_in_room(self, room_name: str, object_label: str) -> Optional[str]:
        """Read an object closest viewpoint from memory."""
        memory_room = self.memory.get(room_name, None)
        if memory_room is None:
            return None

        memory_entity = memory_room.get(object_label.lower(), None)
        if memory_entity is None:
            return None

        return memory_entity.viewpoint

    def write_memory_entities_in_room(
        self, room_name: str, viewpoint: str, extracted_features: list[EmmaExtractedFeatures]
    ) -> None:
        """Write new object entities in memory."""
        for frame_features in extracted_features:
            self._write_frame_entities(
                room_name=room_name, viewpoint=viewpoint, frame_features=frame_features
            )

    def write_inventory_entity_in_room(
        self, room_name: str, viewpoint: str, action: SimBotAction, inventory_entity: str
    ) -> None:
        """Write the new inventory object entity in memory."""
        if not isinstance(action.payload, SimBotObjectInteractionPayload):
            return
        if not action.payload.object.mask:
            return

        self._write(
            room_name=room_name,
            viewpoint=viewpoint,
            object_label=inventory_entity,
            area=get_area_from_compressed_mask(action.payload.object.mask),
        )

    def _write_frame_entities(
        self, room_name: str, viewpoint: str, frame_features: EmmaExtractedFeatures
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
                viewpoint=viewpoint,
                object_label=object_label,
                area=object_area,
            )

    def _write(self, room_name: str, viewpoint: str, object_label: str, area: float) -> None:
        object_label = object_label.lower()
        memory_entity = self.memory[room_name].get(object_label, None)
        if memory_entity is None or memory_entity.area < area:
            self.memory[room_name][object_label] = SimBotMemoryEntity(
                viewpoint=viewpoint, area=area
            )


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
    def from_action(cls, action: SimBotAction, turn_idx: int) -> "SimBotInventory":
        """Instantiate an inventory from the action."""
        if action.adds_object_to_inventory and action.is_successful:
            return cls(entity=action.payload.entity_name, turn_idx=turn_idx)

        if action.removes_object_from_inventory and action.is_successful:
            return cls(entity=None, turn_idx=turn_idx)

        raise AssertionError("Action does not alter/change the inventory in any way")
