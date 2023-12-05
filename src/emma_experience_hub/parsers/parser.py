from typing import Generic, TypeVar


InputType = TypeVar("InputType")
OutputType = TypeVar("OutputType")


class Parser(Generic[InputType, OutputType]):
    """Generic base parser to convert from strings to the output type."""

    def __call__(self, arg: InputType) -> OutputType:
        """Parse the raw text."""
        raise NotImplementedError


class NeuralParser(Parser[str, OutputType]):
    """Base parser for converting output from a neural model to the specified type."""
