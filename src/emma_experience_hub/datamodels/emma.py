from typing import Literal, Optional

import torch
from pydantic import BaseModel

from emma_common.datamodels import EmmaExtractedFeatures


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
