from pydantic import BaseModel, Field

from emma_experience_hub.datamodels.simbot.actions import SimBotAction
from emma_experience_hub.datamodels.simbot.enums import SimBotActionType
from emma_experience_hub.datamodels.simbot.payloads import SimBotObjectOutputType


class SimBotResponse(BaseModel):
    """API response for the SimBot arena."""

    session_id: str = Field(..., alias="sessionId")
    prediction_request_id: str = Field(..., alias="predictionRequestId")
    object_output_type: SimBotObjectOutputType = Field(..., alias="objectOutputType")
    actions: list[SimBotAction] = Field(
        ...,
        max_items=5,
        exclude={
            "__all__": {
                # Do not include fields
                "status": True,
                "raw_output": True,
                "dialog": {"intent"},
            },
        },
    )

    class Config:
        """Config for the model."""

        json_encoders = {
            # When serialising the action type, convert to its base type and then get the name
            SimBotActionType: lambda action_type: action_type.base_type.name,
        }
