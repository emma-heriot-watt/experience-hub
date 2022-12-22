from contextlib import suppress
from typing import Any, Optional, Union

from pydantic import BaseModel, Field, ValidationError, root_validator, validator

from emma_experience_hub.constants.model import END_OF_TRAJECTORY_TOKEN, PREDICTED_ACTION_DELIMITER
from emma_experience_hub.datamodels.simbot.enums import (
    SimBotActionStatusType,
    SimBotActionType,
    SimBotIntentType,
)
from emma_experience_hub.datamodels.simbot.payloads import (
    SimBotDialogPayload,
    SimBotObjectInteractionPayload,
    SimBotObjectOutputType,
    SimBotPayload,
)


class SimBotActionStatus(BaseModel):
    """Status of the previous action taken."""

    id: int = Field(ge=0)
    type: SimBotActionType
    success: bool
    error_type: SimBotActionStatusType = Field(..., alias="errorType")

    @validator("type", pre=True)
    @classmethod
    def convert_action_type_enum(cls, action_type: str) -> str:
        """Check the incoming value for the action type and ensure it will be an enum."""
        # See if the action type is already a value within the enum
        with suppress(ValueError):
            return SimBotActionType(action_type).value

        # See if the action type is already a key within the enum
        with suppress(KeyError):
            return SimBotActionType[action_type].value

        # Otherwise just return it and let it error if it errors
        return action_type

    @validator("error_type", pre=True)
    @classmethod
    def convert_error_type_enum(cls, error_type: str) -> str:
        """Check the incoming value for the error type and ensure it will be an enum."""
        # See if the error type is already a value within the enum
        with suppress(ValueError):
            return SimBotActionStatusType(error_type).value

        # See if the error type is already a key within the enum
        with suppress(KeyError):
            return SimBotActionStatusType[error_type].value

        # Otherwise just return it and let it error if it errors
        return error_type


class SimBotAction(BaseModel):
    """Common SimBot Action which can parse the fields into the specific actions.

    To instantiate the action manually (without using the helper parsers), provide the action
    payload to the `payload` field.

    The `payload` field will _never_ be exported. However, the correct key for the field --- i.e.,
    whatever is expected by the response --- will be. This logic is all outlined within the
    `check_payload_exists_for_all_necessary_keys()` class method.
    """

    id: Optional[int] = Field(ge=0)
    type: SimBotActionType
    payload: SimBotPayload = Field(..., exclude=True)
    status: Optional[SimBotActionStatus] = None

    # The raw output that resulted in the current payload
    raw_output: Optional[str] = None

    class Config:
        """Config for the model."""

        extra = "allow"
        json_encoders = {
            # When serialising the action type, convert to its base type and then get the name
            SimBotActionType: lambda action_type: action_type.base_type.name,
        }

    @root_validator(pre=True)
    @classmethod
    def check_payload_exists_for_all_necessary_keys(
        cls, values: dict[str, Any]  # noqa: WPS110
    ) -> dict[str, Any]:
        """Check the payload for the stated action type exist."""
        raw_action_type = values.get("type")

        if isinstance(raw_action_type, SimBotActionType):
            action_type = raw_action_type
        elif isinstance(raw_action_type, str):
            try:
                action_type = SimBotActionType[raw_action_type]
            except KeyError:
                action_type = SimBotActionType(raw_action_type)
        else:
            raise AssertionError("Unknown action type")

        # Get the correct key for the action payload
        payload_key = action_type.base_type.value.strip()

        # Get the payload from either the `payload` field or the field for the payload_key
        payload: Union[SimBotPayload, dict[str, Any], None] = values.get(
            "payload", values.get(payload_key)
        )

        if payload is None:
            raise AssertionError(
                f"For the given action type `{action_type}`, the expected key for the payload (`{payload_key}`) is not found.",
                f"Available keys: {list(values.keys())}",
            )

        # Parse the payload into the correct instance if necessary
        parsed_payload = (
            payload
            if isinstance(payload, SimBotPayload)
            else action_type.payload_model.parse_obj(payload)
        )

        values["type"] = action_type

        # Set the payload for both the fields
        values[payload_key] = parsed_payload
        values["payload"] = parsed_payload

        return values

    @root_validator
    @classmethod
    def try_convert_base_types_to_aliases(
        cls, values: dict[str, Any]  # noqa: WPS110
    ) -> dict[str, Any]:
        """Convert the action type and payload to the correct alias'd type if there is one."""
        action_type: Optional[SimBotActionType] = values.get("type")
        payload: Optional[SimBotPayload] = values.get("payload")

        # If the action type or the payload doesn't exist, do nothing.
        if not action_type or not payload:
            return values

        possible_aliases = SimBotActionType.base_type_to_aliases().get(action_type)

        # If there are no possible aliases for the current action type, do nothing.
        if not possible_aliases:
            return values

        # Iterate over all the possible alias types to find the right one for the current payload
        for alias_type in possible_aliases:
            try:
                # If the payload can directly be parsed as the alias payload, then it is THAT
                # payload.
                parsed_payload = alias_type.payload_model.parse_obj(payload.dict(by_alias=True))
            except ValidationError:
                continue

            # If there is no exception, update the payload in the values dict
            values["payload"] = parsed_payload

            # Also update the payload for the correct payload key
            values[alias_type.base_type.value.strip()] = parsed_payload

            # Also update action type to the alias too
            values["type"] = alias_type

            # And then break because we don't need to do anything else
            break

        # Return the values, whether or not they have been changed
        return values

    @root_validator
    @classmethod
    def check_id_exists_for_non_sensor_actions(
        cls,
        values: dict[str, Any],  # noqa: WPS110
    ) -> dict[str, Any]:
        """Check that the action has an ID if it is not one of the sensor actions."""
        if values["type"] in SimBotActionType.sensors():
            return values

        action_id = values.get("id")

        if action_id is None:
            raise AssertionError("Action ID should not be None for the given action type.")

        return values

    @validator("raw_output")
    @classmethod
    def ensure_raw_output_ends_in_action_delimiter(
        cls,
        raw_output: Optional[str],
        values: dict[str, Any],  # noqa: WPS110
    ) -> Optional[str]:
        """Ensure the raw output ends in the output delimiter, if it exists."""
        action_type: Optional[SimBotActionType] = values.get("type")

        # If the action type does not exist or the action type is a dialog one
        if not action_type or action_type in SimBotActionType.language():
            return None

        # If the raw output exists, make sure it ends in the predicted action delimiter
        if raw_output and not raw_output.endswith(PREDICTED_ACTION_DELIMITER):
            return f"{raw_output}{PREDICTED_ACTION_DELIMITER}"

        # Otherwise return raw_output
        return raw_output

    @property
    def is_status_known(self) -> bool:
        """Do we know the outcome of the action?"""
        return self.status is not None

    @property
    def is_successful(self) -> bool:
        """Is the action successful?"""
        return self.status.success if self.status is not None else False

    @property
    def is_goto_room(self) -> bool:
        """Is the action for navigating to a room?"""
        return self.type == SimBotActionType.GotoRoom

    @property
    def is_goto_object(self) -> bool:
        """Is the action for navigating to an object?"""
        return self.type == SimBotActionType.GotoObject

    @property
    def is_low_level_navigation(self) -> bool:
        """Is the action for a low-level navigation movement?"""
        return self.type in SimBotActionType.low_level_navigation()

    @property
    def is_object_interaction(self) -> bool:
        """Is the action for interacting with an object?"""
        return self.type in SimBotActionType.object_interaction()

    @property
    def is_dialog(self) -> bool:
        """Is the action a dialog action?"""
        return self.type in SimBotActionType.language()

    @property
    def is_end_of_trajectory(self) -> bool:
        """Does the raw output contain the end-of-trajectory token?"""
        return self.raw_output is not None and END_OF_TRAJECTORY_TOKEN in self.raw_output

    @property
    def object_output_type(self) -> Optional[SimBotObjectOutputType]:
        """Return the object output type used by the action."""
        if self.type == SimBotActionType.Examine:
            if isinstance(self.payload, SimBotObjectInteractionPayload):
                return self.payload.object.object_output_type

        # Otherwise, return the default
        return SimBotObjectOutputType.default()


class SimBotDialogAction(SimBotAction):
    """SimBot action with its fields typed for the dialog payload.

    This is so that we can do less `isinstance` checks.
    """

    payload: SimBotDialogPayload = Field(..., exclude=True)

    @property
    def intent(self) -> SimBotIntentType:
        """Get the intent behind the dialog."""
        return self.payload.intent
