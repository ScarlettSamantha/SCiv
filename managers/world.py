import random
from logging import Logger
from math import sqrt
from typing import TYPE_CHECKING, Dict, Optional, Tuple, Type

from direct.showbase.MessengerGlobal import messenger

from managers.log import LogManager
from managers.player import Player, PlayerManager
from mixins.singleton import Singleton
from system.generators.base import BaseGenerator

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.tiles.base_tile import BaseTile


class World(Singleton):
    logger: Logger = LogManager.get_instance().gameplay.getChild("world")

    def __setup__(self, base):
        self.base = base
        self.hex_radius: float = 0.5
        self.col_spacing: float = 1.4
        self.cols: int = 5
        self.rows: int = 5
        self.middle_x: Optional[float] = None
        self.middle_y: Optional[float] = None
        # Key is the tag, value is the tile.
        self.map: Dict[str, "BaseTile"] = {}
        # Key is the (col, row) tuple, value is the tile.
        self.grid: Dict[Tuple[int, int], "BaseTile"] = {}
        self.generator: Optional[Type[BaseGenerator]] = None
        self.register()

    def __init__(self, base):
        self.base = base

    def register(self):
        self.base.accept(
            "game.gameplay.city.requests_tile",
            self.on_city_requests_tile,
        )

    def generate(self, cols: int, rows: int, radius: float, spacing: float = 1.5):
        self.hex_radius = radius
        self.col_spacing = spacing * self.hex_radius
        self.row_spacing = sqrt(3) * self.hex_radius
        self.cols = cols
        self.rows = rows

        # Compute the middle of the grid.
        self.middle_x = ((cols - 1) * self.col_spacing) / 2.0
        self.middle_y = ((rows - 1) * self.row_spacing) / 2.0

    def lookup_on_tag(self, tag: str) -> Optional["BaseTile"]:
        return self.map.get(tag, None)

    def get_generator(self) -> Optional[Type[BaseGenerator]]:
        if self.generator and issubclass(self.generator, BaseGenerator):
            return self.generator
        return None

    def lookup(self, tag):
        return self.map[tag]

    def random_tile(self) -> "BaseTile":
        return self.grid[random.choice(list(self.grid.keys()))]

    def get_grid(self) -> Dict[Tuple[int, int], "BaseTile"]:
        return self.grid

    def set_ownership_of_tile(self, tile: "BaseTile", player: Player, city: "City"):
        self.logger.info(f"Setting ownership of tile {tile} to {player}")
        old_owner: Optional[Player] = tile.owner
        if old_owner is not None:
            self.logger.info(f"Old owner of tile {tile} is {old_owner}")
            old_owner.tiles.remove(tile)

            if tile.city is not None:
                old_owner.cities.remove(tile.city)

        player.tiles.add(tile)
        tile.owner = player

        if city is not None:  # We don't want to add the city twice
            self.logger.info(f"Adding city {tile.city} to player {player} due to tile ownership change.")
            player.cities.add(city)  # Add the city to the player's cities as its a claim on the tile
            city.player = player
            city.owned_tiles.append(tile)

        self.logger.info(f"Tile {tile} is now owned by {player}, sending message.")
        messenger.send("game.gameplay.tiles.ownership_changed", [tile, player, old_owner])

    def on_city_requests_tile(self, city: "City", tile: "BaseTile"):
        if city.player is None:
            raise AssertionError("City has no player")
        self.logger.info(f"City {city.name} is requesting tile {tile.tag}.")

        can_own_tile: bool = False

        if tile.owner is None:
            # No one owns this tile
            can_own_tile = True
        # Determine if city can claim tile.
        elif tile.owner == PlayerManager.player():
            # Player owns this tile
            can_own_tile = True
        elif tile.owner == PlayerManager.get_nature():
            # Nature owns this tile
            can_own_tile = True
        else:
            # Someone else owns this tile
            can_own_tile = False

        if can_own_tile:
            self.logger.info(f"City {city.name} can own tile {tile.tag}.")
            self.set_ownership_of_tile(tile, city.player, city)
            self.logger.info(f"City {city.name} now owns tile {tile.tag}, sending message")

            self.base.messenger.send(
                "game.gameplay.city.gets_tile_ownership",
                [city, tile],
            )
