import torch

from emma_common.datamodels import (
    DialogueUtterance,
    EmmaPolicyRequest,
    EnvironmentStateTurn,
    SpeakerRole,
    TorchDataMixin,
)
from emma_experience_hub.datamodels import EmmaExtractedFeatures


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

    assert isinstance(
        TorchDataMixin.get_object(TorchDataMixin.to_bytes(features)).bbox_features, torch.Tensor
    )


def test_emma_policy_request_converts_to_bytes_properly() -> None:
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
        dialogue_history=[DialogueUtterance(utterance="look around", role=SpeakerRole.user)],
        environment_history=[EnvironmentStateTurn(features=[features])],
    )

    assert isinstance(
        TorchDataMixin.get_object(TorchDataMixin.to_bytes(emma_policy_request)), EmmaPolicyRequest
    )
