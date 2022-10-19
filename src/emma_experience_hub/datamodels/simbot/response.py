from pydantic import BaseModel, Field

from emma_experience_hub.datamodels.simbot.actions import SimBotAction, SimBotActionType
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
                # Do not include the status field
                "status": True,
                # Do not include the intent field for the dialog action
                "dialog": {"intent"},
            },
        },
    )

    class Config:
        """Config for the model."""

        json_encoders = {
            # Use the action type name when converting to the JSON response
            SimBotActionType: lambda action_type: action_type.name,
        }
