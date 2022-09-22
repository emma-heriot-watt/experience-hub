import torch

from emma_experience_hub.datamodels import EmmaExtractedFeatures


def test_emma_extracted_features_works_as_expected() -> None:
    features = EmmaExtractedFeatures(
        bbox_features=torch.randn(3, 10),
        bbox_coords=torch.randn(3, 10),
        bbox_probas=torch.randn(3, 10),
        cnn_features=torch.randn(3, 10),
    )

    assert features
