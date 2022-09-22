import torch
from numpy.typing import ArrayLike
from pydantic import BaseModel


class EmmaExtractedFeatures(BaseModel, arbitrary_types_allowed=True):
    """Extracted features from an image."""

    bbox_features: torch.Tensor
    bbox_coords: torch.Tensor
    bbox_probas: torch.Tensor
    cnn_features: torch.Tensor

    @classmethod
    def from_raw_response(cls, raw_response: dict[str, ArrayLike]) -> "EmmaExtractedFeatures":
        """Instantiate the features from the raw response data.

        Dict keys that are used below can be found within the emma-simbot/perception repo.
        """
        return cls(
            bbox_features=torch.tensor(raw_response["bbox_features"]),
            bbox_coords=torch.tensor(raw_response["bbox_coords"]),
            bbox_probas=torch.tensor(raw_response["bbox_probas"]),
            cnn_features=torch.tensor(raw_response["cnn_features"]),
        )
