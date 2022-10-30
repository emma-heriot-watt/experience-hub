from typing import Any, Literal, Optional

import torch
from pydantic import BaseModel


class EmmaExtractedFeatures(BaseModel):
    """Extracted features from an image."""

    bbox_features: torch.Tensor
    bbox_coords: torch.Tensor
    bbox_probas: torch.Tensor
    cnn_features: torch.Tensor
    class_labels: list[str]
    width: int
    height: int

    class Config:
        """Config for the Model."""

        arbitrary_types_allowed = True
        json_encoders = {
            torch.Tensor: lambda tensor: tensor.tolist(),
            "Tensor": lambda tensor: tensor.tolist(),
        }

    @classmethod
    def from_raw_response(cls, raw_response: dict[str, Any]) -> "EmmaExtractedFeatures":
        """Instantiate the features from the raw response data.

        Dict keys that are used below can be found within the emma-simbot/perception repo.
        """
        return cls(
            bbox_features=torch.tensor(raw_response["bbox_features"]),
            bbox_coords=torch.tensor(raw_response["bbox_coords"]),
            bbox_probas=torch.tensor(raw_response["bbox_probas"]),
            cnn_features=torch.tensor(raw_response["cnn_features"]),
            class_labels=raw_response["class_labels"],
            width=raw_response["width"],
            height=raw_response["height"],
        )


class DialogueUtterance(BaseModel):
    """Single utterance model for the Emma Policy client."""

    utterance: str
    role: Literal["user", "agent"]


class EnvironmentStateTurn(BaseModel):
    """State of the environment at a single timestep."""

    features: list[EmmaExtractedFeatures]
    output: Optional[str] = None

    class Config:
        """Config for the Model."""

        json_encoders = {
            torch.Tensor: lambda tensor: tensor.tolist(),
            "Tensor": lambda tensor: tensor.tolist(),
        }


class EmmaPolicyRequest(BaseModel):
    """Request model for the Emma Policy client."""

    dialogue_history: list[DialogueUtterance]
    environment_history: list[EnvironmentStateTurn]

    class Config:
        """Config for the Model."""

        json_encoders = {
            torch.Tensor: lambda tensor: tensor.tolist(),
            "Tensor": lambda tensor: tensor.tolist(),
        }
