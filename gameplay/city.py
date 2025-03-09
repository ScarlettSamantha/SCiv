from logging import Logger
from typing import TYPE_CHECKING, List, Optional

from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger

from gameplay.citizens import Citizens
from gameplay.improvement import Improvement
from gameplay.improvements import Improvements
from managers.log import LogManager
from system.entity import BaseEntity

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.tiles.base_tile import BaseTile


class City(BaseEntity, DirectObject):
    logger: Logger = LogManager.get_instance().gameplay.getChild("city")

    def __init__(self, name: str, tile: "BaseTile", *args, **kwargs):
        super().__init__(*args, **kwargs)
        from gameplay.player import Player

        self.name: str = name
        self.player: Optional[Player] = None
        self.tile: BaseTile = tile
        self.owned_tiles: List[BaseTile] = [self.tile]
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

        self.register()

    def register(self):
        messenger.accept("game.gameplay.city.gets_tile_ownership", self, self.on_tile_ownership_changed)

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

    def assign_tile(self, tile: "BaseTile"):
        self.owned_tiles.append(tile)

    def deassign_tile(self, tile: "BaseTile"):
        self.owned_tiles.remove(tile)

    def destroy(self): ...

    def on_tile_ownership_changed(self, city: "City", tile: "BaseTile"):
        self.logger.debug(f"City {city.name} is being told that tile {tile.tag} has changed ownership.")
        if city != self and tile not in self.owned_tiles:
            # This does not concern us
            return
        elif city == self and tile not in self.owned_tiles:
            self.assign_tile(tile)  # We now own this tile.
        elif city == self and tile in self.owned_tiles:
            self.deassign_tile(tile)  # We are being told that we no longer own this tile.

    @classmethod
    def found_new(
        cls,
        name: str,
        tile: "BaseTile",
        owner: "Player",
        population: int = 1,
        is_capital: bool = False,
        auto_claim_radius: int = 0,
    ) -> "City":
        instance = City(name=name, tile=tile)
        instance.player = owner
        instance.population = population
        instance.is_capital = is_capital
        tile.city = instance
        tile.city_owner = instance

        if auto_claim_radius > 0:
            from gameplay.repositories.tile import TileRepository

            neighbours: List[BaseTile] = TileRepository.get_neighbors(
                tile,
                auto_claim_radius,
                check_passable=False,
            )
            for neighbour in neighbours:
                cls.logger.debug(f"City {instance.name} is requesting claiming tile {neighbour.tag}, sending message.")
                messenger.send("game.gameplay.city.requests_tile", [instance, neighbour])

        return instance
