from typing import TYPE_CHECKING, Dict, Optional

from mixins.singleton import Singleton

if TYPE_CHECKING:
    from gameplay.unit import Unit
    from main import SCIV


class UnitManager(Singleton):
    def __setup__(self, base: "SCIV"):
        self.base: "SCIV" = base
        self.units: Dict[str, "Unit"] = {}

    def __init__(self, base: "SCIV"):
        self.base: "SCIV" = base

    def all(self) -> Dict[str, "Unit"]:
        return self.units

    def find_unit(self, tag: str) -> Optional["Unit"]:
        return self.units.get(tag, None)

    def exists(self, tag: str) -> bool:
        return tag in self.units

    def add_unit(self, unit: "Unit"):
        self.units[str(unit.tag)] = unit

    def remove_unit(self, unit: "Unit"):
        if not hasattr(unit, "tag"):  # This is a bug
            return
        del self.units[str(unit.tag)]

    def reset(self):
        self.units = {}

    def load(self, data: Dict[str, "Unit"]):
        self.units = data
