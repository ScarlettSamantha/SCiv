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

        self.vision_offset_layout: str = "odd-q"
        self._vision_radius_tile_tags_cache: Dict[Tuple[int, int, int, str], Set[str]] = {}
        self._unit_vision_source_signatures: Dict[str, Tuple[str, int, str]] = {}
        self._pending_vision_updates_by_player_tag: Dict[str, Set[str]] = {}
        self._pending_vision_players_by_tag: Dict[str, "Player"] = {}
        self._turn_active_tile_tags: Set[str] = set()
        self._turn_active_tile_index_dirty: bool = True
        self._vision_update_flush_scheduled: bool = False

        self.register()

    def __init__(self, base: "OpenCiv"):
        self.base: "OpenCiv" = base

    def reset(self):
        from helpers.model import ModelHelper

        self.map = {}
        self.grid = {}
        self.effects = Effects(self)
        self._vision_radius_tile_tags_cache = {}
        self._unit_vision_source_signatures = {}
        self._pending_vision_updates_by_player_tag = {}
        self._pending_vision_players_by_tag = {}
        self._vision_update_flush_scheduled = False
        self._turn_active_tile_tags = set()
        self._turn_active_tile_index_dirty = True

        unit: "Unit"
        for unit in list(EntityManager.get_singleton_instance().get_all(EntityType.UNIT).values()):  # type: ignore
            unit.destroy()

        tile: "Tile"
        for tile in list(EntityManager.get_singleton_instance().get_all(EntityType.TILE).values()):  # type: ignore
            tile.destroy()

        ModelHelper.reset()

    def load(self, data: Dict[str, "Tile"]):
        self.logger.info("Loading world data.")
        self._vision_radius_tile_tags_cache = {}

        for map_item in data.values():
            item_tag: str | None = map_item.tag # type: ignore this can happen if we load a tile that has no tag, which should not happen but we want to be safe about it
            if item_tag is None: # type: ignore
                self.logger.warning(f"Map item {map_item} has no tag, skipping.")
                continue
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
        self.accept("game.gameplay.unit.destroyed.context", self.on_unit_destroyed)
        self.accept("system.unit.destroyed.context", self.on_unit_destroyed)
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
        self._unit_vision_source_signatures = {}
        self._vision_radius_tile_tags_cache = {}
        self._turn_active_tile_tags = set()
        self._turn_active_tile_index_dirty = True

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
        self.advance_all_player_vision_lingering()

        if self._turn_active_tile_index_dirty:
            self._refresh_turn_active_tile_index()

        for tile_tag in list(self._turn_active_tile_tags):
            tile = self.map.get(tile_tag)
            if tile is None:
                self._turn_active_tile_tags.discard(tile_tag)
                continue

            if not self._tile_requires_turn_processing(tile):
                self._turn_active_tile_tags.discard(tile_tag)
                continue

            tile.on_turn_end(turn)

            if not self._tile_requires_turn_processing(tile):
                self._turn_active_tile_tags.discard(tile_tag)

        self.effects.on_turn_end(turn)

    def refresh_player_vision(self, player: "Player") -> None:
        linger_turns = player.get_vision_linger_turns()
        player.vision.set_default_linger_turns(linger_turns)

        visible_tiles: Set["Tile"] = set(player.collect_visible_tiles())
        visible_tiles.update(self._resolve_tiles_from_tags(player.vision.get_reveal_tile_tags()))

        changed_tiles = player.vision.recompute_visible_tiles(visible_tiles, linger_turns)
        changed_tiles.update(self._sync_player_unit_vision_sources(player))

        messenger.send("game.gameplay.vision.updated", [player, changed_tiles])

    def advance_player_vision_lingering(self, player: "Player") -> Set[str]:
        player.vision.set_default_linger_turns(player.get_vision_linger_turns())
        changed_tiles = player.vision.advance_lingering_tiles()

        if changed_tiles:
            messenger.send("game.gameplay.vision.updated", [player, changed_tiles])

        return changed_tiles

    def advance_all_player_vision_lingering(self) -> None:
        for player in PlayerManager.all(add_mechanic_players=True).values():
            self.advance_player_vision_lingering(player)

    def reveal_tiles_for_player(
        self,
        player: "Player | str",
        source_id: str,
        tiles: Iterable["Tile | str"] | "Tile | str",
    ) -> None:
        resolved_player = self._resolve_player(player)
        normalized_tiles = self._normalize_reveal_targets(tiles)
        changed_tiles = self._update_reveal_source_for_player(resolved_player, source_id, normalized_tiles)

        if changed_tiles is None:
            if resolved_player.vision.set_reveal_source(source_id, normalized_tiles):
                self.refresh_player_vision(resolved_player)
            return

        if changed_tiles:
            messenger.send("game.gameplay.vision.updated", [resolved_player, changed_tiles])

    def clear_reveal_tiles_for_player(self, player: "Player | str", source_id: str) -> None:
        resolved_player = self._resolve_player(player)
        changed_tiles = self._update_reveal_source_for_player(resolved_player, source_id, [])

        if changed_tiles is None:
            if resolved_player.vision.clear_reveal_source(source_id):
                self.refresh_player_vision(resolved_player)
            return

        if changed_tiles:
            messenger.send("game.gameplay.vision.updated", [resolved_player, changed_tiles])

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
        self._register_turn_active_tile(unit.get_tile())
        self.refresh_unit_vision(unit)

    def on_unit_moved(self, unit: "Unit", tile: "Tile | None" = None, old_tile: "Tile | None" = None) -> None:
        self._register_turn_active_tile(tile)
        self._register_turn_active_tile(old_tile)
        self._register_turn_active_tile(unit.get_tile())
        self.refresh_unit_vision(unit)

    def on_unit_destroyed(
        self,
        unit: "Unit",
        destroyed_tile: "Tile | None" = None,
        destroyed_owner: "Player | None" = None,
    ) -> None:
        if destroyed_owner is None:
            return

        source_id = f"unit:{unit.get_tag()}"
        self._unit_vision_source_signatures.pop(source_id, None)
        changed_tiles = self._update_reveal_source_for_player(destroyed_owner, source_id, [])

        if changed_tiles is None:
            return

        if changed_tiles:
            messenger.send("game.gameplay.vision.updated", [destroyed_owner, changed_tiles])

    def _tile_requires_turn_processing(self, tile: "Tile") -> bool:
        return (
            tile.player is not None
            or tile.is_city()
            or len(tile.units) > 0
            or len(tile.effects) > 0
            or len(tile.improvements()) > 0
            or tile.needs_tile_processing is True
        )


    def _register_turn_active_tile(self, tile: "Tile | None") -> None:
        if tile is None:
            return

        tile_tag = tile.get_tag()
        if tile_tag:
            self._turn_active_tile_tags.add(tile_tag)


    def _refresh_turn_active_tile_index(self) -> None:
        self._turn_active_tile_tags = {
            tile.get_tag()
            for tile in self.map.values()
            if self._tile_requires_turn_processing(tile)
        }
        self._turn_active_tile_index_dirty = False


    def on_city_founded(self, city: "City") -> None:
        self._register_turn_active_tile(city.get_tile())
        self.refresh_player_vision(city.get_owner())

    def on_tile_ownership_changed(self, tile: "Tile", player: "Player", old_owner: "Player | None") -> None:
        self._register_turn_active_tile(tile)
        self.refresh_player_vision(player)

    def on_request_reveal_tiles(
        self,
        player: "Player | str",
        source_id: str,
        tiles: Iterable["Tile | str"] | "Tile | str",
    ) -> None:
        self.reveal_tiles_for_player(player, source_id, tiles)

    def on_request_clear_reveal_tiles(self, player: "Player | str", source_id: str) -> None:
        self.clear_reveal_tiles_for_player(player, source_id)

    def refresh_unit_vision(self, unit: "Unit") -> bool:
        player = unit.get_owner()
        changed_tiles = self._update_unit_vision_source(unit)

        if changed_tiles is None:
            return False

        if changed_tiles:
            messenger.send("game.gameplay.vision.updated", [player, changed_tiles])

        return True

    def _sync_player_unit_vision_sources(self, player: "Player") -> Set[str]:
        changed_tiles: Set[str] = set()

        for unit in player.get_all_units():
            unit_changed_tiles = self._update_unit_vision_source(unit)
            if unit_changed_tiles is not None:
                changed_tiles.update(unit_changed_tiles)

        return changed_tiles

    def _update_unit_vision_source(self, unit: "Unit") -> Set[str] | None:
        player = unit.get_owner()
        updater = getattr(player.vision, "update_reveal_source_tiles", None)

        if not callable(updater):
            return None

        player.vision.set_default_linger_turns(player.get_vision_linger_turns())

        radius = self._get_unit_vision_radius(unit)
        unit_tile = unit.get_tile()
        source_id = f"unit:{unit.get_tag()}"
        signature = (player.get_tag(), radius, unit_tile.get_tag())
        cached_signature = self._unit_vision_source_signatures.get(source_id)
        vision_has_signature = getattr(player.vision, "has_reveal_source_signature", None)

        if cached_signature == signature:
            if not callable(vision_has_signature) or vision_has_signature(source_id, signature):
                return set()

        visible_tile_tags = self._tile_tags_in_radius_by_math(unit_tile, radius)
        self._unit_vision_source_signatures[source_id] = signature

        return cast(
            Set[str],
            updater(
                source_id=source_id,
                tiles_or_tags=visible_tile_tags,
                signature=signature,
            ),
        )

    def _update_reveal_source_for_player(
        self,
        player: "Player",
        source_id: str,
        tiles_or_tags: Iterable["Tile | str"],
    ) -> Set[str] | None:
        updater = getattr(player.vision, "update_reveal_source_tiles", None)

        if not callable(updater):
            return None

        player.vision.set_default_linger_turns(player.get_vision_linger_turns())

        return cast(
            Set[str],
            updater(
                source_id=source_id,
                tiles_or_tags=tiles_or_tags,
            ),
        )

    def _get_unit_vision_radius(self, unit: "Unit") -> int:
        return max(0, int(unit.get_vision_range()))

    def _tiles_in_radius_by_math(self, origin: "Tile", radius: int) -> Set["Tile"]:
        return self._resolve_tiles_from_tags(self._tile_tags_in_radius_by_math(origin, radius))

    def _tile_tags_in_radius_by_math(self, origin: "Tile", radius: int) -> Set[str]:
        safe_radius = max(0, int(radius))
        cache_key = (int(origin.x), int(origin.y), safe_radius, self.vision_offset_layout)
        cached_tags = self._vision_radius_tile_tags_cache.get(cache_key)

        if cached_tags is not None:
            return set(cached_tags)

        origin_cube = self._offset_to_cube(int(origin.x), int(origin.y))
        tile_tags: Set[str] = set()

        for dx in range(-safe_radius, safe_radius + 1):
            min_dy = max(-safe_radius, -dx - safe_radius)
            max_dy = min(safe_radius, -dx + safe_radius)

            for dy in range(min_dy, max_dy + 1):
                dz = -dx - dy
                q, r = self._cube_to_offset(
                    origin_cube[0] + dx,
                    origin_cube[1] + dy,
                    origin_cube[2] + dz,
                )

                tile = self.grid.get((q, r))
                if tile is not None:
                    tile_tags.add(tile.get_tag())

        self._vision_radius_tile_tags_cache[cache_key] = tile_tags
        return set(tile_tags)

    def _offset_to_cube(self, q: int, r: int) -> Tuple[int, int, int]:
        if self.vision_offset_layout == "even-q":
            cube_x = q
            cube_z = r - (q + (q & 1)) // 2
            cube_y = -cube_x - cube_z
            return cube_x, cube_y, cube_z

        cube_x = q
        cube_z = r - (q - (q & 1)) // 2
        cube_y = -cube_x - cube_z
        return cube_x, cube_y, cube_z

    def _cube_to_offset(self, cube_x: int, cube_y: int, cube_z: int) -> Tuple[int, int]:
        if self.vision_offset_layout == "even-q":
            q = cube_x
            r = cube_z + (cube_x + (cube_x & 1)) // 2
            return q, r

        q = cube_x
        r = cube_z + (cube_x - (cube_x & 1)) // 2
        return q, r

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
