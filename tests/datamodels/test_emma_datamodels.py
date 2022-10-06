import orjson
import torch

from emma_experience_hub.datamodels import EmmaExtractedFeatures
from emma_experience_hub.datamodels.emma import (
    DialogueUtterance,
    EmmaPolicyRequest,
    EnvironmentStateTurn,
)


def test_emma_extracted_features_parses_correctly() -> None:
    features = EmmaExtractedFeatures(
        bbox_features=torch.randn(3, 10),
        bbox_coords=torch.randn(3, 10),
        bbox_probas=torch.randn(3, 10),
        cnn_features=torch.randn(3, 10),
        class_labels=["label1", "label2"],
        width=100,
        height=300,
    )

    assert features


def test_emma_extracted_features_converts_to_json_properly() -> None:
    features = EmmaExtractedFeatures(
        bbox_features=torch.randn(3, 10),
        bbox_coords=torch.randn(3, 10),
        bbox_probas=torch.randn(3, 10),
        cnn_features=torch.randn(3, 10),
        class_labels=["label1", "label2"],
        width=100,
        height=300,
    )

    assert features

    assert isinstance(orjson.loads(features.json())["bbox_features"], list)


def test_emma_policy_request_converts_to_json_properly() -> None:
    features = EmmaExtractedFeatures(
        bbox_features=torch.randn(3, 10),
        bbox_coords=torch.randn(3, 10),
        bbox_probas=torch.randn(3, 10),
        cnn_features=torch.randn(3, 10),
        class_labels=["label1", "label2"],
        width=100,
        height=300,
    )

    emma_policy_request = EmmaPolicyRequest(
        dialogue_history=[DialogueUtterance(utterance="look around", role="user")],
        environment_history=[EnvironmentStateTurn(features=[features])],
    )

    request_json = emma_policy_request.json(models_as_dict=False)

    assert request_json
