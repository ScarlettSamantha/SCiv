from typing import TYPE_CHECKING, Any, Self, Set

from sciv.gameplay.citizen import Citizen

if TYPE_CHECKING:
    from gameplay.citizen import Citizen

default_population_expontent: float = 1.5
default_food_requirement: float = 10


def population_curve(
    x: float, exponent: float = default_population_expontent, base_food_requirement: float = default_food_requirement
) -> float:
    # f(1)=10; then as x increases, f(x) = 10 + (x-1)^exponent
    return base_food_requirement + (x - 1) ** exponent


class Citizens:
    def __init__(self):
        super().__init__()
        self._citizens: Set["Citizen"] = set()

    def add(self, value: "Citizen", as_birth: bool = True) -> None:
        self._citizens.add(value)

    def remove(self, value: "Citizen | int" = 1, as_death: bool = True) -> None:
        if isinstance(value, int):
            for _ in range(value):
                self._citizens.pop()
        else:
            self._citizens.remove(value)

    def reset(self) -> None:
        self._citizens: Set["Citizen"] = set()

    def create(self, num: int = 1, *args: Any, **kwargs: Any) -> None:
        def _create(self: Self, *args: Any, **kwargs: Any) -> None:
            self.add(value=Citizen(*args, **kwargs))

        for _ in range(num):
            _create(self=self, *args, **kwargs)

    def __add__(self, value: Citizen):
        self.add(value=value)

    def __len__(self) -> int:
        return len(self._citizens)

    def dump(self) -> dict[str, Any]:
        return {
            "citizens": [citizen.dump() for citizen in self._citizens],
            "num_citizens": len(self._citizens),
        }

    def load_state(self):
        from gameplay.citizen import Citizen

        self._citizens = set()
        for citizen_data in self.dump().get("citizens", []):
            citizen: Citizen = Citizen.__new__(Citizen)
            citizen.load_state(citizen_data)
            self.add(value=citizen, as_birth=False)
