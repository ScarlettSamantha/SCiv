from typing import TYPE_CHECKING, Optional

from gameplay.citizens import Citizens
from gameplay.improvement import Improvement
from gameplay.improvements import Improvements
from system.entity import BaseEntity

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.tiles.base_tile import BaseTile


class City(BaseEntity):
    def __init__(self, name: str, tile: "BaseTile"):
        from gameplay.player import Player

        self.name: str = name
        self.player: Optional[Player] = None
        self.tile: BaseTile = tile
        self.is_capital: bool = False

        self.active: bool = True
        self.destroyed: bool = False
        self.population: int = 1

        self.citizens: Citizens = Citizens()

        self.revolting: bool = False
        self.being_sieged: bool = False
        self.being_blockaded: bool = False

        self.health: int = 100
        self.max_health: int = 100

        self.tax_level: float = 0.0

        self._improvements: Improvements = Improvements()

        # @todo
        self.spies = []

        if self.player is not None:
            self._register_object()

    def build(self, improvement: Improvement):
        self._improvements.add(improvement)

    def promote_to_capital(self):
        self.is_capital = True

    def _register_object(self):
        if self.player is not None:
            self.player.cities.add(self)
            if self.is_capital:
                self.player.capital = self

    def birth(self, population: int = 1, *args, **kwargs):
        for i in range(population):
            self.citizens.create(*args, **kwargs)

    def _register_callbacks(self):
        self.citizens.register_callback("on_birth", self.on_citizen_birth)

    def on_citizen_birth(self, citizen):
        self.population += 1

    def de_capitalize(self):
        self.is_capital = False

    @classmethod
    def found_new(
        cls, name: str, tile: "BaseTile", owner: "Player", population: int = 1, is_capital: bool = False
    ) -> "City":
        instance = City(name=name, tile=tile)
        instance.player = owner
        instance.population = population
        instance.is_capital = is_capital
        return instance
