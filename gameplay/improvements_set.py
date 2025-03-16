from typing import List, Optional, Type

from gameplay.improvement import Improvement


class ImprovementsSet:
    def __init__(self, improvements: Optional[List] = None):
        self._improvements: List[Improvement] = []
        self._num_improvements: int = 0

        if improvements is not None:
            for item in improvements:
                self.add(item)

    def add(self, value: Improvement):
        self._improvements.append(value)
        self._num_improvements += 1

    def __add__(self, value: Improvement):
        self.add(value)
        return self

    def get_all(self) -> List[Improvement]:
        return self._improvements

    def remove(self, value: Improvement):
        self._improvements.remove(value)
        self._num_improvements -= 1

    def has(self, value: Improvement | Type[Improvement]) -> bool:
        if isinstance(value, type):
            return any(isinstance(i, value) for i in self._improvements)
        return value in self._improvements

    def __contains__(self, a) -> bool:
        if isinstance(a, type):
            return any(isinstance(i, a) for i in self._improvements)
        return a in self._improvements

    def __len__(self) -> int:
        return self._num_improvements

    def on_turn_end(self, turn: int):
        for item in self._improvements:
            item.on_turn_end(turn)
