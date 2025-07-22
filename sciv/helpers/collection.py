from collections import deque
from typing import Deque, Generic, Iterator, TypeVar

T = TypeVar("T")


class BoundedStack(Generic[T]):
    def __init__(self, limit: int) -> None:
        self._data: Deque[T] = deque(maxlen=limit)

    def push(self, item: T) -> None:
        self._data.append(item)

    def pop(self) -> T:
        return self._data.pop()

    def peek(self) -> T:
        return self._data[-1]

    def __len__(self) -> int:
        return len(self._data)

    def is_empty(self) -> bool:
        return not self._data

    def __iter__(self) -> Iterator[T]:
        return iter(self._data)

    def to_list(self) -> list[T]:
        return list(self._data)
