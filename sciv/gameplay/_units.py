from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional, Set, TypeVar, cast
from weakref import ReferenceType, ref

from helpers.debug import Debug

if TYPE_CHECKING:
    from gameplay.unit import Unit

T = TypeVar("T", bound="Unit")


class Units:
    def __init__(self):
        self._units: Set[ReferenceType[Unit]] = set()
        self._num_units: int = 0

    def add_unit(self, unit: "Unit") -> None:
        for _unit in self._units:
            for existing_unit in self._units:
                _existing_unit: "Unit" = cast("Unit", existing_unit())
                assert _existing_unit is not None, "Existing unit reference is None"
                if _existing_unit.get_tag() == unit.get_tag:
                    raise ValueError(f"Unit with tag {unit.tag} already exists in this Units instance.")

        self._units.add(ref(unit))
        self._num_units += 1

    def remove_unit(self, unit: "Unit") -> None:
        for existing_unit in self._units:
            _existing_unit: "Unit" = cast("Unit", existing_unit())
            assert _existing_unit is not None, "Existing unit reference is None"
            if _existing_unit.get_tag() == unit.get_tag():
                self._units.remove(existing_unit)
                self._num_units -= 1
                return

        if Debug.system_units():
            raise ValueError(f"Unit with tag {unit.get_tag()} does not exist in this Units instance.")

    def __len__(self) -> int:
        return len(self._units)

    def __contains__(self, unit: "Unit") -> bool:
        return unit in self._units

    def all(self) -> Set["Unit"]:
        units: Set["Unit"] = set()
        for unit_ref in self._units:
            unit: "Unit" = cast("Unit", unit_ref())
            assert unit is not None, "Unit reference is None"
            units.add(unit)
        return units

    def all_weak(self) -> Set[ReferenceType["Unit"]]:
        return self._units

    def has(self, unit: Optional["Unit"] = None) -> bool:
        if unit is None:
            return self.has_any()
        return unit in self._units

    def has_any(self) -> bool:
        return len(self._units) > 0

    def first(self) -> Optional["Unit"]:
        if self._units:
            item: ReferenceType[Unit] = next(iter(self._units))  # Return an arbitrary unit without removing it
            return cast("Unit", item())
        return None

    def __iter__(self) -> Iterator["Unit"]:
        for unit_ref in self._units:
            unit: "Unit" = cast("Unit", unit_ref())
            assert unit is not None, "Unit reference is None"
            yield unit

    def count(self) -> int:
        return len(self._units)

    def dump(self) -> Dict[str, Any]:
        return {
            "units": [unit.get_tag() for unit in self.all()],
            "num_units": self._num_units,
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        from managers.entity import EntityManager, EntityType

        self._num_units = 0
        self._units: Set[ReferenceType[Unit]] = set()
        if isinstance(state, dict):  # type: ignore
            state = state.get("units", [])
        for unit_tag in state:
            unit: ReferenceType["Unit"] | None = cast(
                ReferenceType["Unit"] | None,
                EntityManager.get_singleton_instance().get_ref_weak(EntityType.UNIT, unit_tag),
            )
            assert unit is not None, f"Unit with tag {unit_tag} not found in EntityManager."
            self._units.add(unit)
            self._num_units += 1
