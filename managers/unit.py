from typing import TYPE_CHECKING, Dict, Optional

from mixins.singleton import Singleton

if TYPE_CHECKING:
    from gameplay.units.unit_base import UnitBaseClass


class Unit(Singleton):
    def __setup__(self, base):
        self.base = base
        self.units: Dict[str, "UnitBaseClass"] = {}

    def __init__(self, base):
        self.base = base

    def find_unit(self, tag: str) -> Optional["UnitBaseClass"]:
        return self.units.get(tag, None)

    def exists(self, tag: str) -> bool:
        return tag in self.units

    def add_unit(self, unit: "UnitBaseClass"):
        self.units[str(unit.tag)] = unit

    def remove_unit(self, unit: "UnitBaseClass"):
        del self.units[str(unit.tag)]

    def reset(self):
        self.units = {}

    def load(self, data: Dict[str, "UnitBaseClass"]):
        self.units = data
