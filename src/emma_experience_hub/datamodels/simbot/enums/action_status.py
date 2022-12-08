from enum import Enum


class SimBotActionStatusType(Enum):
    """Possible action status types returned from subsequent requests."""

    action_successful = "ActionSuccessful"
    unsupported_action = "UnsupportedAction"
    unsupported_navigation = "UnsupportedNavigation"
    already_holding_object = "AlreadyHoldingObject"
    receptacle_is_full = "ReceptacleIsFull"
    receptacle_is_closed = "ReceptacleIsClosed"
    target_inaccessible = "TargetInaccessible"
    killed_by_hazard = "KilledByHazard"
    target_out_of_range = "TargetOutOfRange"
    alternate_navigation_used = "AlternateNavigationUsed"
    object_unpowered = "ObjectUnpowered"
    object_overloaded = "ObjectOverloaded"
    invalid_command = "InvalidCommand"
    object_not_picked_up = "ObjectNotPickedUp"
    arena_unavailable = "ArenaUnavailable"
    incorrect_action_format = "IncorrectActionFormat"
    invalid_object_class = "InvalidObjectClass"
    action_execution_error = "ActionExecutionError"
    post_process_error = "PostProcessError"

    @classmethod
    def reverse_mapping(cls) -> dict[str, str]:
        """Create a reversed mapping of the enum."""
        return {element.value: element.name for element in cls}
