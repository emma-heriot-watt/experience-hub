import torch
from pytest_cases import param_fixture

from emma_common.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.simbot import SimBotActionType


def create_placeholder_features_frames() -> list[EmmaExtractedFeatures]:
    frame1 = {
        "bbox_features": torch.tensor(
            [
                [1, 2, 3],
                [4, 5, 6],
            ]
        ),
        "bbox_coords": torch.tensor(
            [
                [25, 42, 74, 80],
                [12, 35, 24, 56],
            ]
        ),
        "bbox_probas": torch.tensor([[0.35, 0.2, 0.25, 0.2], [0.2, 0.35, 0.25, 0.2]]),
        "cnn_features": torch.tensor([1, 2]),
        "class_labels": ["label1", "label2"],
        "entity_labels": ["label1", "label2"],
        "width": 300,
        "height": 300,
    }

    frame2 = {
        "bbox_features": torch.tensor([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
        "bbox_coords": torch.tensor(
            [[65, 42, 72, 90], [48, 195, 54, 216], [125, 35, 150, 72]],
        ),
        "bbox_probas": torch.tensor([[0.2, 0.2, 0.35, 0.25], [0.2, 0.2, 0.25, 0.35]]),
        "cnn_features": torch.tensor([1, 2]),
        "class_labels": ["label3", "label4"],
        "entity_labels": ["label3", "label4"],
        "width": 300,
        "height": 300,
    }
    return [EmmaExtractedFeatures.parse_obj(frame1), EmmaExtractedFeatures.parse_obj(frame2)]


simbot_object_name = param_fixture(
    "simbot_object_name",
    ["Apple", "Sticky Note", "Machine Panel"],
    # sorted(get_simbot_object_label_to_class_name_map().keys()),
    scope="session",
)

simbot_non_parsable_object_name = param_fixture(
    "simbot_non_parsable_object_name",
    ["red button", "white board", "chicken banana"],
    scope="session",
)

simbot_interaction_action = param_fixture(
    "simbot_interaction_action",
    [action.name for action in SimBotActionType.object_interaction()],
    scope="session",
)

simbot_extracted_features = param_fixture(
    "simbot_extracted_features",
    [create_placeholder_features_frames()],
    scope="session",
)
