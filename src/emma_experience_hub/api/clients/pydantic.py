from typing import Any, Generic, TypeVar

import orjson
from pydantic import BaseModel


PydanticT = TypeVar("PydanticT", bound=BaseModel)


def default(py_obj: Any) -> Any:
    """Conform non-JSON serializable types."""
    # Handle sets
    if isinstance(py_obj, set):
        return list(py_obj)

    raise TypeError


class PydanticClientMixin(Generic[PydanticT]):
    """Client mixin with Pydantic-specific methods to make handling Pydantic models easier."""

    model: type[PydanticT]

    def _pydantic_to_bytes(self, data: PydanticT) -> bytes:
        """Convert the pydantic model to bytes."""
        return orjson.dumps(
            data.dict(),
            option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY,
            default=default,
        )

    def _pydantic_from_bytes(self, data: bytes) -> PydanticT:
        """Convert bytes to the pydantic model."""
        return self.model.parse_obj(orjson.loads(data))
