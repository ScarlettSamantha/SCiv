from typing import TYPE_CHECKING, Iterator, List, cast
from weakref import ReferenceType, ref

if TYPE_CHECKING:
    from gameplay.city import City


class Cities:
    def __init__(self) -> None:
        self._cities: List[ReferenceType["City"]] = []
        self.index: int = 0

    def add(self, value: "City") -> None:
        if value not in self._cities:
            self._cities.append(ref(value))

    def remove(self, value: "City", auto_destroy: bool = True) -> None:
        self._cities.remove(ref(value))
        if auto_destroy:
            value.destroy()

    def all(self) -> List["City"]:
        cities: List["City"] = []
        for city_ref in self._cities:
            city: "City" = cast("City", city_ref())
            assert city is not None, "City reference is None"
            cities.append(city)
        return cities

    def all_weak(self) -> List[ReferenceType["City"]]:
        return self._cities

    def has(self, value: "City") -> bool:
        return value in self._cities

    def __contains__(self, value: "City") -> bool:
        return self.has(value)

    def __iter__(self) -> Iterator["City"]:
        return iter(self.all())

    def __len__(self) -> int:
        return len(self._cities)

    def __next__(self) -> "City":
        if self.index >= len(self._cities):
            raise StopIteration
        city: "City" = cast("City", self._cities[self.index]())
        self.index += 1
        return city

    def count(self) -> int:
        return len(self._cities)

    def dump(self) -> List[str]:
        cities_tags: List[str] = []
        for city in self.all():
            assert city is not None, "City reference is None"
            cities_tags.append(city.get_tag())
        return cities_tags

    def load_state(self, state: List[str]) -> None:
        from managers.entity import EntityManager, EntityType

        cities: List[ReferenceType["City"]] = []
        i = 0
        for city_tag in state:
            city: ReferenceType["City"] = cast(
                ReferenceType["City"],
                EntityManager.get_singleton_instance().get_ref(EntityType.CITY, city_tag, weak_ref=True),
            )
            cities.append(city)
            i += 1

        if i != len(state):
            raise ValueError(f"Expected {len(state)} cities, but found {i}.")

        self._cities: List[ReferenceType["City"]] = cities
        self.index = len(self._cities)
