from collections import deque
from collections.abc import Iterable
from enum import Enum
from typing import Generic, TypeVar

from pydantic import Field
from pydantic.generics import GenericModel


QueueType = TypeVar("QueueType")


class QueueSide(Enum):
    """Refer to a specific side of the queue."""

    head = "head"
    tail = "tail"


class SimBotQueue(GenericModel, Generic[QueueType], validate_assignment=True):
    """Generic queue which can be used to track multiple aspects.

    A deque object is used for the queue, and multiple methods are used to allow for consistnet
    interactions with the queue.
    """

    queue: deque[QueueType] = Field(default_factory=deque)
    popped_elements_count: int = 0

    @property
    def is_not_empty(self) -> bool:
        """Detect whether the queue is empty or not."""
        return bool(len(self.queue))

    def __len__(self) -> int:
        """Get the total number of elements in the queue."""
        return len(self.queue)

    def reset(self) -> None:
        """Reset the queue."""
        self.queue.clear()
        self.popped_elements_count = 0  # noqa: WPS601

    def pop_from_head(self) -> QueueType:
        """Pop the next element from the head of the queue."""
        return self._pop(side=QueueSide.head)

    def pop_from_tail(self) -> QueueType:
        """Pop the next element from the tail of the queue."""
        return self._pop(side=QueueSide.tail)

    def append_to_head(self, element: QueueType) -> None:
        """Append the element to the head of the queue."""
        return self._append(element, side=QueueSide.head)

    def append_to_tail(self, element: QueueType) -> None:
        """Append the element to from the tail of the queue."""
        return self._append(element, side=QueueSide.tail)

    def extend_head(self, elements: Iterable[QueueType]) -> None:
        """Add multiple elements to the head of the queue IN REVERSE ORDER.

        Each element will be added to the head one by one, which will reverse the order of the
        elements in the list once they're in the queue.
        """
        return self._extend(elements, side=QueueSide.head)

    def extend_tail(self, elements: Iterable[QueueType]) -> None:
        """Add multiple elements to the tail of the queue."""
        return self._extend(elements, side=QueueSide.tail)

    def _pop(self, side: QueueSide) -> QueueType:
        """Pop an element from the queue."""
        if side == QueueSide.head:
            element = self.queue.popleft()
        if side == QueueSide.tail:
            element = self.queue.pop()

        # Increase the number of popped elements by 1
        self.popped_elements_count += 1  # noqa: WPS601
        return element

    def _append(self, element: QueueType, side: QueueSide) -> None:
        """Append an element to the given side of the queue."""
        if side == QueueSide.head:
            return self.queue.appendleft(element)
        if side == QueueSide.tail:
            return self.queue.append(element)

        raise NotImplementedError(f"Cannot append to the provided side ({side})")

    def _extend(self, elements: Iterable[QueueType], side: QueueSide) -> None:
        """Add multiple elements to the queue."""
        if side == QueueSide.head:
            return self.queue.extendleft(elements)
        if side == QueueSide.tail:
            return self.queue.extend(elements)

        raise NotImplementedError(f"Cannot add elements to the provided side ({side})")
