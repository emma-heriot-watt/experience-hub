from collections.abc import Iterable

import numpy as np

from emma_experience_hub.datamodels.common import Position


def get_closest_position_index_to_reference(
    reference: Position, coordinate_list: Iterable[Position]
) -> int:
    """Get the index of the closest position to the reference."""
    # Convert Positions to numpy arrays
    coordinate_list_array = np.asarray([position.as_list() for position in coordinate_list])
    reference_array = np.asarray(reference.as_list())

    # Determine the euclidean distance between each agent and their coords
    delta_to_reference = coordinate_list_array - reference_array
    distances = np.einsum("ij,ij->i", delta_to_reference, delta_to_reference)
    # Get the index of the closest viewpoint
    index = np.argmin(distances)

    return int(index)
