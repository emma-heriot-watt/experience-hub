from contextlib import suppress
from typing import Generic, Optional, TypeVar, Union

from pydantic import validator
from pydantic.generics import GenericModel

from emma_experience_hub.datamodels.simbot.enums import SimBotActionType, SimBotIntentType


T = TypeVar("T", bound=SimBotIntentType)


class SimBotIntent(GenericModel, Generic[T]):
    """Model represenating the intent behind the utterance."""

    type: T
    action: Optional[SimBotActionType] = None
    entity: Optional[str] = None

    @validator("type", pre=True)
    @classmethod
    def convert_intent_type_enum(
        cls, intent_type: Union[str, SimBotIntentType]
    ) -> Union[str, SimBotIntentType]:
        """Check the incoming value for the intent type and ensure it will be an enum."""
        if isinstance(intent_type, str):
            # See if the intent type is already a value within the enum
            with suppress(ValueError):
                return SimBotIntentType(intent_type)

            # See if the intent type is already a key within the enum
            with suppress(KeyError):
                return SimBotIntentType[intent_type]

        # Otherwise just return it and let it error if it errors
        return intent_type
