from typing import Any, List, Self

from gameplay.citizen import Citizen
from mixins.callbacks import CallbacksMixin

default_population_expontent: float = 1.5
default_food_requirement: float = 10


def population_curve(
    x: float, exponent: float = default_population_expontent, base_food_requirement: float = default_food_requirement
) -> float:
    # f(1)=10; then as x increases, f(x) = 10 + (x-1)^exponent
    return base_food_requirement + (x - 1) ** exponent


class Citizens(CallbacksMixin):
    def __init__(self):
        super().__init__()
        self._citizens: List[Citizen] = []
        self.register_citizen_events()

    def register_citizen_events(self) -> None:
        self._declare_event(event="on_birth")

    def add(self, value: Citizen, as_birth: bool = True) -> None:
        self._citizens.append(value)
        if as_birth:
            self.trigger_all_callbacks(category="on_birth", citizen=value)

    def remove(self, value: Citizen | int = 1, as_death: bool = True) -> None:
        if isinstance(value, int):
            for _ in range(value):
                self._citizens.pop()
        else:
            self._citizens.remove(value)

        if as_death:
            self.trigger_all_callbacks(category="on_death", citizen=value)

    def reset(self) -> None:
        self._citizens: List[Citizen] = []

    def create(self, num: int = 1, *args: Any, **kwargs: Any) -> None:
        def _create(self: Self, *args: Any, **kwargs: Any) -> None:
            self.add(value=Citizen(*args, **kwargs))

        for _ in range(num):
            _create(self=self, *args, **kwargs)

    def __add__(self, value: Citizen):
        self.add(value=value)

    def __len__(self) -> int:
        return len(self._citizens)
