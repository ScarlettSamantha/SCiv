from typing import TYPE_CHECKING, Dict, Optional

from mixins.singleton import Singleton

if TYPE_CHECKING:
    from gameplay.unit import Unit

    from sciv.game import OpenCiv


class UnitManager(Singleton):
    def __setup__(self, base: "OpenCiv"):
        self.base: "OpenCiv" = base
        self.units: Dict[str, "Unit"] = {}
        self.by_player: Dict[str, Dict[str, "Unit"]] = {}

    def __init__(self, base: "OpenCiv"):
        self.base: "OpenCiv" = base

    def all(self) -> Dict[str, "Unit"]:
        return self.units

    def find_unit(self, tag: str) -> Optional["Unit"]:
        return self.units.get(tag, None)

    def exists(self, tag: str) -> bool:
        return tag in self.units

    def add_unit(self, unit: "Unit"):
        self.units[str(unit.tag)] = unit
        if str(unit.owner.tag) not in self.by_player:  # type: ignore
            self.by_player[str(unit.owner.tag)] = {}  # type: ignore
        self.by_player[str(unit.owner.tag)][str(unit.tag)] = unit  # type: ignore

    def remove_unit(self, unit: "Unit"):
        if not hasattr(unit, "tag"):  # This is a bug
            return
        if str(unit.tag) in self.units:
            del self.units[str(unit.tag)]

    def reset(self):
        self.units = {}

    def load(self, data: Dict[str, "Unit"]):
        for unit in data.values():
            unit.load_state()
            self.add_unit(unit)

        for unit in self.units.values():
            if not hasattr(unit, "tag"):
                continue
            if str(unit.tag) not in self.by_player:
                self.by_player[str(unit.tag)] = {}
            self.by_player[str(unit.get_owner().get_tag())][str(unit.tag)] = unit

            unit.spawn()
