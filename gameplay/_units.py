from typing import TYPE_CHECKING, Generic, List, TypeVar

if TYPE_CHECKING:
    from gameplay.units.unit_base import UnitBaseClass

T = TypeVar("T", bound="UnitBaseClass")


class Units(Generic[T]):
    def __init__(self):
        self._units: List[T] = []
        self._num_units: int = 0

    def add_unit(self, unit: T) -> None:
        self._units.append(unit)
        self._num_units += 1

    def remove_unit(self, unit: T):
        if unit in self._units:
            self._units.remove(unit)
        self._num_units -= 1

    def __len__(self) -> int:
        return self._num_units

    def all(self) -> List[T]:
        return self._units

    def has(self, unit: T) -> bool:
        return unit in self._units

    def has_any(self) -> bool:
        return len(self._units) > 0
