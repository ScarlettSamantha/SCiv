from typing import TYPE_CHECKING, Generic, List, TypeVar

if TYPE_CHECKING:
    from gameplay.units.unit_base import UnitBaseClass

T = TypeVar("T", bound="UnitBaseClass")


class Units(Generic[T]):
    def __init__(self):
        self.units: List[T] = []

    def add_unit(self, unit: T) -> None:
        self.units.append(unit)

    def remove_unit(self, unit: T):
        if unit in self.units:
            self.units.remove(unit)

    def __len__(self):
        return len(self.units)
