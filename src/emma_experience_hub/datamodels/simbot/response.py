from pydantic import BaseModel, Field, validator

from emma_experience_hub.common.settings import SimBotSettings
from emma_experience_hub.datamodels.simbot.actions import SimBotAction
from emma_experience_hub.datamodels.simbot.enums import SimBotActionType
from emma_experience_hub.datamodels.simbot.payloads import SimBotObjectOutputType


settings = SimBotSettings.from_env()


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

    @validator("actions")
    @classmethod
    def add_highlight_before_object_interactions(
        cls, actions: list[SimBotAction]
    ) -> list[SimBotAction]:
        """If the feature is enabled, add a highlight action before every interaction action."""
        if not settings.feature_flags.enable_always_highlight_before_object_action:
            return actions

        updated_actions: list[SimBotAction] = []

        for action in actions:
            # Only add a highlight before we are interacting with an object
            if action.is_object_interaction or action.is_goto_object:
                # Don't add a highlight before highlight actions
                if action.type != SimBotActionType.Highlight:
                    highlight_action = SimBotAction(
                        id=len(actions),
                        type=SimBotActionType.Highlight,
                        payload=action.payload,
                        raw_output="highlight object debug",
                    )
                    updated_actions.append(highlight_action)

            updated_actions.append(action)

        return updated_actions
