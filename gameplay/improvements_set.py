from typing import List, Optional

from gameplay.improvement import Improvement


class ImprovementsSet:
    def __init__(self, improvements: Optional[List] = None):
        self._improvements = []

        if improvements is not None:
            for item in improvements:
                self.add(item)

    def add(self, value: Improvement):
        self._improvements.append(value)

    def __add__(self, value: Improvement):
        self.add(value)
        return self

    def get_all(self) -> List[Improvement]:
        return self._improvements

    def __contains__(self, a) -> bool:
        if isinstance(a, type):
            return any(isinstance(i, a) for i in self._improvements)
        return a in self._improvements
