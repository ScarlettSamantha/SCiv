from __future__ import annotations
from typing import List

from gameplay.units.classes._base import UnitBaseClass


class Units:
    def __init__(self):
        self.units: List[UnitBaseClass] = []

    def add_unit(self, unit: UnitBaseClass):
        self.units.append(unit)

    def remove_unit(self, unit: UnitBaseClass):
        self.units.remove(unit)

    def __len__(self):
        return len(self.units)
