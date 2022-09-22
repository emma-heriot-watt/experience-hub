from typing import Literal

from pydantic import BaseModel, Field

from emma_experience_hub.datamodels.simbot.actions import SimBotAction


class SimBotResponse(BaseModel):
    """API response for the SimBot arena."""

    session_id: str = Field(..., alias="sessionId")
    prediction_request_id: str = Field(..., alias="predictionRequestId")
    object_output_type: Literal["OBJECT_CLASS", "OBJECT_MASK"] = Field(
        ..., alias="objectOutputType"
    )
    actions: list[SimBotAction] = Field(..., max_items=5)
