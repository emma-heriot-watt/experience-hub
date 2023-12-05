from typing import Optional

from pydantic import BaseModel


class SimBotPayload(BaseModel):
    """Base payload for SimBot payloads."""

    @property
    def entity_name(self) -> Optional[str]:  # noqa: WPS324
        """Try to get the name of the entity."""
        # I don't know why this the noqa's are necessary here, but they are.
        return None  # noqa: WPS324
