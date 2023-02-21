from typing import Literal, Optional, Union, overload

import torch
from loguru import logger
from opentelemetry import trace
from pydantic import BaseModel, Field

from emma_experience_hub.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.simbot.payloads import SimBotObjectMaskType
from emma_experience_hub.functions.simbot.masks import compress_segmentation_mask


tracer = trace.get_tracer(__name__)


class SimBotSceneObjectTokens(BaseModel):
    """Token IDs when we find an object in the scene."""

    frame_index: int = Field(default=1, gt=0)
    object_index: Optional[int] = Field(default=None, gt=0)


def extract_index_from_special_token(token: str) -> int:
    """Extract the token index from a special token."""
    return int(token.strip().split("_")[-1].replace(">", ""))


@overload
def get_mask_from_special_tokens(
    frame_index: int,
    object_index: int,
    extracted_features: list[EmmaExtractedFeatures],
    return_coords: Literal[False] = False,
) -> SimBotObjectMaskType:
    ...  # noqa: WPS428


@overload
def get_mask_from_special_tokens(
    frame_index: int,
    object_index: int,
    extracted_features: list[EmmaExtractedFeatures],
    return_coords: Literal[True],
) -> tuple[SimBotObjectMaskType, tuple[float, ...]]:
    ...  # noqa: WPS428


def get_mask_from_special_tokens(
    frame_index: int,
    object_index: int,
    extracted_features: list[EmmaExtractedFeatures],
    return_coords: bool = False,
) -> Union[SimBotObjectMaskType, tuple[SimBotObjectMaskType, tuple[float, ...]]]:
    """Get the object mask from the visual token."""
    # Get the bbox coordinates for the correct frame index
    object_coordinates_bbox = extracted_features[frame_index - 1].bbox_coords

    # Get the coordinates for the specified object
    (x_min, y_min, x_max, y_max) = object_coordinates_bbox[object_index - 1].tolist()

    # Create an empty mask for the object
    mask = torch.zeros(
        (
            extracted_features[frame_index - 1].width,
            extracted_features[frame_index - 1].height,
        )
    )

    # Populate the bbox region in the mask
    mask[int(y_min) : int(y_max) + 1, int(x_min) : int(x_max) + 1] = 1  # noqa: WPS221

    with tracer.start_as_current_span("Compress segmentation mask"):
        compressed_mask = compress_segmentation_mask(mask)

    if return_coords:
        return compressed_mask, (x_min, y_min, x_max, y_max)
    return compressed_mask


def get_class_name_from_special_tokens(
    frame_index: int,
    object_index: int,
    extracted_features: list[EmmaExtractedFeatures],
) -> str:
    """Get the object class name from the visual token."""
    # Get the class labels for the correct frame index
    object_class_labels = extracted_features[frame_index - 1].entity_labels

    if not object_class_labels:
        raise AssertionError("Entity labels do not exist for features")

    # Get the class label for the specified object
    return object_class_labels[object_index - 1]


def get_correct_frame_index(
    parsed_frame_index: int, num_frames_in_current_turn: int, num_total_frames: int
) -> int:
    """Get the correct frame index, considering the number of frames in the current turn."""
    # Get the starting index frame for the current turn
    start_frame_index = num_total_frames - num_frames_in_current_turn + 1

    # Get the corrected frame index
    frame_index = parsed_frame_index - start_frame_index
    if num_frames_in_current_turn == 1 and frame_index != 0:
        logger.warning(f"Predicted frame index: {frame_index} instead of 0.")
        frame_index = 0
    else:
        # Make sure that the predicted frame index is between 0 and 3.
        frame_index = min(max(frame_index, 0), 3)
    return frame_index
