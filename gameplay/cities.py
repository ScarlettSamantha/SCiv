from typing import TYPE_CHECKING, Iterator, List

if TYPE_CHECKING:
    from gameplay.city import City


class Cities:
    def __init__(self) -> None:
        self._cities: List["City"] = []

    def add(self, value: "City") -> None:
        if value not in self._cities:
            self._cities.append(value)

    def remove(self, value: "City", auto_destroy: bool = True) -> None:
        self._cities.remove(value)
        if auto_destroy:
            value.destroy()

    def has(self, value: "City") -> bool:
        return value in self._cities

    def __iter__(self) -> Iterator["City"]:
        self.index = 0
        return self

    def __len__(self) -> int:
        return len(self._cities)

    def __next__(self) -> "City":
        if self.index >= len(self._cities):
            raise StopIteration
        city: "City" = self._cities[self.index]
        self.index += 1
        return city
