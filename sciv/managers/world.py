from collections.abc import Iterable
import random
import weakref
from logging import Logger
from math import sqrt
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple, Type, cast

from direct.showbase import MessengerGlobal
from direct.showbase.DirectObject import DirectObject
from direct.showbase.MessengerGlobal import messenger
from gameplay.repositories.tile import TileRepository
from managers.entity import EntityManager, EntityType
from managers.log import LogManager
from managers.player import PlayerManager
from mixins.singleton import Singleton
from system.effects import Effects

if TYPE_CHECKING:
    from game import OpenCiv
    from gameplay.city import City
    from gameplay.effect import Effect
    from gameplay.improvement import Improvement
    from gameplay.tile import Tile
    from gameplay.unit import Unit
    from managers.player import Player
    from system.generators.base import BaseGenerator


class World(Singleton, DirectObject):
    logger: Logger = LogManager.get_singleton_instance().gameplay.getChild("world")

    def __setup__(self, base: "OpenCiv", *args: Any, **kwargs: Any):
        self.base = base
        self.hex_radius: float = 0.5
        self.col_spacing: float = 1.4
        self.cols: int = 5
        self.rows: int = 5
        self.middle_x: Optional[float] = None
        self.middle_y: Optional[float] = None
        self.map: Dict[str, "Tile"] = {}
        self.grid: Dict[Tuple[int, int], "Tile"] = {}
        self.generator: Optional[Type["BaseGenerator"]] = None
        self.effects: Effects = Effects(self)
        self.register()

    def __init__(self, base: "OpenCiv"):
        self.base: "OpenCiv" = base

    def reset(self):
        from helpers.model import ModelHelper

        self.map = {}
        self.grid = {}
        self.effects = Effects(self)

        unit: "Unit"
        for unit in list(EntityManager.get_singleton_instance().get_all(EntityType.UNIT).values()):  # type: ignore
            unit.destroy()

        tile: "Tile"
        for tile in list(EntityManager.get_singleton_instance().get_all(EntityType.TILE).values()):  # type: ignore
            tile.destroy()

        ModelHelper.reset()

    def load(self, data: Dict[str, "Tile"]):
        self.logger.info("Loading world data.")
        for map_item in data.values():
            item_tag: str | None = map_item.tag
            self.map[item_tag] = map_item

        self.grid = {(tile.x, tile.y): tile for tile in self.map.values()}
        self.logger.info("World data loaded.")
        self.logger.info("Calculating world size")
        self.cols = max([tile.x for tile in self.map.values()]) + 1
        self.rows = max([tile.y for tile in self.map.values()]) + 1
        self.calculate_middle()
        self.logger.info(f"World size is {self.cols}x{self.rows}")
        TileRepository.grid = self.grid

        for improvement in cast(
            List["Improvement"], EntityManager.get_singleton_instance().get_all(EntityType.IMPROVEMENT).values()
        ):  # type: ignore
            improvement.load_state()

        for city in cast(Dict[str, "City"], EntityManager.get_singleton_instance().get_all(EntityType.CITY)).values():
            city.load_state()

        for effect in cast(List["Effect"], EntityManager.get_singleton_instance().get_all(EntityType.EFFECT).values()):  # type: ignore
            effect.load_state()

        for tile in self.map.values():
            tile.load_state()

    def calculate_middle(self):
        self.middle_x = self.cols / 2.0
        self.middle_y = self.rows / 2.0

    def register(self):
        self.accept(  # type: ignore
            "game.gameplay.city.requests_tile",
            self.on_city_requests_tile,
        )
        self.accept("game.gameplay.unit.spawned", self.on_unit_spawned)
        self.accept("game.gameplay.unit.moved", self.on_unit_moved)
        self.accept("game.gameplay.unit.destroyed", self.on_unit_destroyed)
        self.accept("system.unit.destroyed", self.on_unit_destroyed)
        self.accept("game.gameplay.city.founded", self.on_city_founded)
        self.accept("game.gameplay.tiles.ownership_changed", self.on_tile_ownership_changed)
        self.accept("game.gameplay.vision.request_reveal_tiles", self.on_request_reveal_tiles)
        self.accept("game.gameplay.vision.request_clear_reveal_tiles", self.on_request_clear_reveal_tiles)

    def get_size(self) -> Tuple[int, int]:
        return self.cols, self.rows

    def generate(self, cols: int, rows: int, radius: float, spacing: float = 1.5):
        self.hex_radius = radius
        self.col_spacing = spacing * self.hex_radius
        self.row_spacing = sqrt(3) * self.hex_radius
        self.cols = cols
        self.rows = rows

        self.middle_x = ((cols - 1) * self.col_spacing) / 2.0
        self.middle_y = ((rows - 1) * self.row_spacing) / 2.0

        TileRepository.reset_caches()
        TileRepository.grid = self.grid

    def lookup_on_tag(self, tag: str) -> Optional["Tile"]:
        return self.map.get(tag, None)

    def get_generator(self) -> Optional[Type["BaseGenerator"]]:
        if self.generator:
            return self.generator
        return None

    def lookup(self, tag: str) -> "Tile":
        return self.map[tag]

    def random_tile(self) -> "Tile":
        return self.grid[random.choice(list(self.grid.keys()))]

    def get_grid(self) -> Dict[Tuple[int, int], "Tile"]:
        return self.grid

    def get_grid_reference(self) -> weakref.ReferenceType[Dict[Tuple[int, int], "Tile"]]:
        return weakref.ref(self.grid)

    def on_turn_end(self, turn: int):
        self.refresh_all_player_vision()

        for tile in self.map.values():
            if (
                tile.player is not None
                or tile.is_city()
                or len(tile.units) > 0
                or len(tile.effects) > 0
                or len(tile._improvements) > 0  # type: ignore
                or tile.needs_tile_proecessing is True
            ):
                tile.on_turn_end(turn)
        self.effects.on_turn_end(turn)

    def refresh_player_vision(self, player: "Player") -> None:
        linger_turns = player.get_vision_linger_turns()
        player.vision.set_default_linger_turns(linger_turns)
        visible_tiles: Set["Tile"] = set(player.collect_visible_tiles())
        visible_tiles.update(self._resolve_tiles_from_tags(player.vision.get_reveal_tile_tags()))
        changed_tiles = player.vision.recompute_visible_tiles(visible_tiles, linger_turns)
        messenger.send("game.gameplay.vision.updated", [player, changed_tiles])

    def reveal_tiles_for_player(
        self,
        player: "Player | str",
        source_id: str,
        tiles: Iterable["Tile | str"] | "Tile | str",
    ) -> None:
        resolved_player = self._resolve_player(player)
        if resolved_player.vision.set_reveal_source(source_id, self._normalize_reveal_targets(tiles)):
            self.refresh_player_vision(resolved_player)

    def clear_reveal_tiles_for_player(self, player: "Player | str", source_id: str) -> None:
        resolved_player = self._resolve_player(player)
        if resolved_player.vision.clear_reveal_source(source_id):
            self.refresh_player_vision(resolved_player)

    def refresh_all_player_vision(self) -> None:
        for player in PlayerManager.all(add_mechanic_players=True).values():
            self.refresh_player_vision(player)

    def set_ownership_of_tile(self, tile: "Tile", player: "Player", city: "City"):
        self.logger.info(f"Setting ownership of tile {tile} to {player}")
        old_owner: Optional["Player"] = tile.get_owner() if tile.owner is not None else None
        if old_owner is not None:
            self.logger.info(f"Old owner of tile {tile} is {old_owner}")
            old_owner.tiles.remove(tile)

            if tile.city is not None:
                if tile.is_city():
                    old_owner.cities.remove(tile.city)  # type: ignore
                else:
                    tile.city_owner = None

            if tile.city_owner is not None:
                _city: City | None = tile.city_owner()
                assert _city is not None, "City owner reference is None, it has been destroyed."
                _city.owned_tiles.remove(tile) if city else None
                tile.city_owner = None

        player.tiles.add(tile)
        tile.city_owner = weakref.ref(city)
        tile.owner = player

        if tile.is_city():
            self.logger.info(f"Adding city {tile.city} to player {player} due to tile ownership change.")
            city.player = player
        city.owned_tiles.append(tile)

        self.logger.info(f"Tile {tile} is now owned by {player}, sending message.")
        messenger.send("game.gameplay.tiles.ownership_changed", [tile, player, old_owner])

    def on_city_requests_tile(self, city: "City", tile: "Tile"):
        if city.player is None:
            raise AssertionError("City has no player")
        if isinstance(tile, weakref.ReferenceType):
            tile = tile()  # type: ignore its a weak reference
            assert tile is not None, "Tile reference is None, it has been destroyed."
        elif isinstance(tile, str):
            tile = self.lookup(tile)
        self.logger.info(f"City {city.name} is requesting tile {tile.tag}.")

        can_own_tile: bool = False

        if tile.owner is None:
            can_own_tile = True
        elif tile.owner == PlayerManager.player():
            can_own_tile = True
        elif tile.owner == PlayerManager.get_nature():
            can_own_tile = True
        else:
            can_own_tile = False

        if can_own_tile:
            self.logger.info(f"City {city.name} can own tile {tile.get_tag()}.")
            self.set_ownership_of_tile(tile, city.player, city)
            self.logger.info(f"City {city.name} now owns tile {tile.get_tag()}, sending message")

            MessengerGlobal.messenger.send("game.gameplay.city.gets_tile_ownership", [city, tile])
            MessengerGlobal.messenger.send(
                f"game.gameplay.city.gets_tile_ownership_{city.tag}",
                [city, tile],
            )

    def on_unit_spawned(self, unit: "Unit") -> None:
        self.refresh_player_vision(unit.get_owner())

    def on_unit_moved(self, unit: "Unit", tile: "Tile", old_tile: "Tile | None" = None) -> None:
        self.refresh_player_vision(unit.get_owner())

    def on_unit_destroyed(self, unit: "Unit") -> None:
        self.refresh_all_player_vision()

    def on_city_founded(self, city: "City") -> None:
        self.refresh_player_vision(city.get_owner())

    def on_tile_ownership_changed(self, tile: "Tile", player: "Player", old_owner: "Player | None") -> None:
        self.refresh_player_vision(player)
        if old_owner is not None and old_owner != player:
            self.refresh_player_vision(old_owner)

    def on_request_reveal_tiles(
        self,
        player: "Player | str",
        source_id: str,
        tiles: Iterable["Tile | str"] | "Tile | str",
    ) -> None:
        self.reveal_tiles_for_player(player, source_id, tiles)

    def on_request_clear_reveal_tiles(self, player: "Player | str", source_id: str) -> None:
        self.clear_reveal_tiles_for_player(player, source_id)

    def _resolve_player(self, player: "Player | str") -> "Player":
        if not isinstance(player, str):
            return player

        for candidate in PlayerManager.all(add_mechanic_players=True).values():
            if candidate.tag == player:
                return candidate

        raise KeyError(f"Unknown player requested for vision reveal: {player}")

    def _normalize_reveal_targets(
        self,
        tiles: Iterable["Tile | str"] | "Tile | str",
    ) -> List["Tile | str"]:
        if isinstance(tiles, str):
            return [tiles]

        if hasattr(tiles, "get_tag"):
            return [cast("Tile | str", tiles)]

        return [tile for tile in cast(Iterable["Tile | str"], tiles)]

    def _resolve_tiles_from_tags(self, tile_tags: Iterable[str]) -> Set["Tile"]:
        resolved_tiles: Set["Tile"] = set()
        for tile_tag in tile_tags:
            tile = self.lookup_on_tag(tile_tag)
            if tile is not None:
                resolved_tiles.add(tile)
        return resolved_tiles
