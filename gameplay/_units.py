from typing import TYPE_CHECKING, Iterator, List, Optional, TypeVar

if TYPE_CHECKING:
    from gameplay.units.unit_base import UnitBaseClass

T = TypeVar("T", bound="UnitBaseClass")


class Units:
    def __init__(self):
        self._units: List[UnitBaseClass] = []
        self._num_units: int = 0

    def add_unit(self, unit: "UnitBaseClass") -> None:
        self._units.append(unit)
        self._num_units += 1

    def remove_unit(self, unit: "UnitBaseClass"):
        if unit in self._units:
            self._units.remove(unit)
            self._num_units -= 1

    def __len__(self) -> int:
        return self._num_units

    def all(self) -> List["UnitBaseClass"]:
        return self._units

    def has(self, unit: Optional["UnitBaseClass"] = None) -> bool:
        if unit is None:
            return self.has_any()
        return unit in self._units

    def has_any(self) -> bool:
        return len(self._units) > 0

    def first(self) -> Optional["UnitBaseClass"]:
        if self._units:
            return self._units[0]
        return None

    def __iter__(self) -> Iterator["UnitBaseClass"]:
        return iter(self._units)
