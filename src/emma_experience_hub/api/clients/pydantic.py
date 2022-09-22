from typing import Generic, TypeVar

import orjson
from pydantic import BaseModel


PydanticT = TypeVar("PydanticT", bound=BaseModel)


class PydanticClient(Generic[PydanticT]):
    """Base client with Pydantic-specific methods to make handling Pydantic models easier."""

    model: type[PydanticT]

    def _pydantic_to_bytes(self, data: PydanticT) -> bytes:
        """Convert the pydantic model to bytes."""
        return orjson.dumps(data, option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY)

    def _pydantic_from_bytes(self, data: bytes) -> PydanticT:
        """Convert bytes to the pydantic model."""
        return self.model.parse_obj(orjson.loads(data))
