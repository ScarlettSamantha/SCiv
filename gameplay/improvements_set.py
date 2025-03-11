from typing import List, Optional

from gameplay.improvement import Improvement


class ImprovementsSet:
    def __init__(self, improvements: Optional[List] = None):
        self._improvements = {}
        if improvements is not None:
            for item in improvements:
                self.add(item)

    def add(self, value: Improvement):
        self._improvements[len(self._improvements.keys())] = value

    def __add__(self, value: Improvement):
        self.add(value)
        return self

    def get_all(self) -> List[Improvement]:
        return list(self._improvements.values())

    def __contains__(self, a) -> bool:
        return a in self._improvements.values()
