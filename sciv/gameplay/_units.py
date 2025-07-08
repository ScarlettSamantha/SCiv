from typing import TYPE_CHECKING, Iterator, Optional, Set, TypeVar

if TYPE_CHECKING:
    from gameplay.unit import Unit

T = TypeVar("T", bound="Unit")


class Units:
    def __init__(self):
        self._units: Set[Unit] = set()
        self._num_units: int = 0

    def add_unit(self, unit: "Unit") -> None:
        for unit in self._units:
            if unit.tag == unit.tag:
                return
        self._units.add(unit)
        self._num_units += 1

    def remove_unit(self, unit: "Unit"):
        for unit in list(self._units):
            if unit.tag == unit.tag:
                self._units.remove(unit)
                break
        self._num_units -= 1

    def to_dict(self) -> object:
        return {
            "_units": list(self._units),
            "_num_units": self._num_units,
        }

    def __len__(self) -> int:
        return len(self._units)

    def __contains__(self, unit: "Unit") -> bool:
        return unit in self._units

    def all(self) -> Set["Unit"]:
        return self._units

    def has(self, unit: Optional["Unit"] = None) -> bool:
        if unit is None:
            return self.has_any()
        return unit in self._units

    def has_any(self) -> bool:
        return len(self._units) > 0

    def first(self) -> Optional["Unit"]:
        if self._units:
            return next(iter(self._units))  # Return an arbitrary unit without removing it
        return None

    def __iter__(self) -> Iterator["Unit"]:
        return iter(self._units)

    def count(self) -> int:
        return len(self._units)

    def dump(self) -> dict[str, object]:
        return {
            "units": [unit.get_tag() for unit in self._units],
            "num_units": self._num_units,
        }
