from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Protocol, Set, TypeVar, cast
from weakref import ReferenceType, ref

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.improvement import Improvement
    from gameplay.resource import BaseResource
    from gameplay.terrain._base_terrain import BaseTerrain
    from gameplay.tile import Tile
    from gameplay.unit import Unit


T = TypeVar("T")


class VisionTileLike(Protocol):
    def get_tag(self) -> str: ...


def collect_radius_visibility(origin: T, radius: int, neighbor_getter: Callable[[T, int], Iterable[T]]) -> Set[T]:
    visible_tiles: Set[T] = {origin}
    if radius <= 0:
        return visible_tiles

    visible_tiles.update(neighbor_getter(origin, radius))
    return visible_tiles


def expand_border_visibility(core_tiles: Iterable[T], border_radius: int, neighbor_getter: Callable[[T], Iterable[T]]) -> Set[T]:
    visible_tiles: Set[T] = set(core_tiles)
    frontier: Set[T] = set(visible_tiles)

    if border_radius <= 0:
        return visible_tiles

    for _ in range(border_radius):
        next_frontier: Set[T] = set()
        for tile in frontier:
            next_frontier.update(neighbor_getter(tile))

        next_frontier -= visible_tiles
        if not next_frontier:
            break

        visible_tiles.update(next_frontier)
        frontier = next_frontier

    return visible_tiles


class VisionTileState(str, Enum):
    UNSEEN = "unseen"
    VISIBLE = "visible"
    LINGERING = "lingering"
    FOGGED = "fogged"


def is_visible_for_render(state: VisionTileState) -> bool:
    return state in {VisionTileState.VISIBLE, VisionTileState.LINGERING}


def build_tile_visibility_states(vision: "Vision", tiles: Iterable[VisionTileLike]) -> Dict[str, VisionTileState]:
    visibility_states: Dict[str, VisionTileState] = {}

    for tile in tiles:
        tile_tag = tile.get_tag()
        visibility_states[tile_tag] = vision.get_tile_state(tile_tag)

    return visibility_states


@dataclass(slots=True)
class VisionTileRecord:
    tile_tag: str
    state: VisionTileState
    turns_remaining: int = 0

    @property
    def is_visible(self) -> bool:
        return self.state in {VisionTileState.VISIBLE, VisionTileState.LINGERING}

    @property
    def is_explored(self) -> bool:
        return self.state is not VisionTileState.UNSEEN

    def dump(self) -> Dict[str, Any]:
        return {
            "tile_tag": self.tile_tag,
            "state": self.state.value,
            "turns_remaining": self.turns_remaining,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisionTileRecord":
        raw_state = str(data.get("state", VisionTileState.FOGGED.value))
        try:
            state = VisionTileState(raw_state)
        except ValueError:
            state = VisionTileState.FOGGED

        return cls(
            tile_tag=str(data.get("tile_tag", "")),
            state=state,
            turns_remaining=max(0, int(data.get("turns_remaining", 0))),
        )


class Vision:
    DEFAULT_LINGER_TURNS: int = 2

    def __init__(self, linger_turns: int = DEFAULT_LINGER_TURNS):
        self.default_linger_turns: int = max(0, linger_turns)
        self._tile_records: Dict[str, VisionTileRecord] = {}
        self._tile_refs: Dict[str, ReferenceType["Tile"]] = {}
        self._reveal_sources: Dict[str, Set[str]] = {}
        self._changed_tile_tags: Set[str] = set()
        self._visible_tiles: Set[ReferenceType["Tile"]] = set()
        self._visible_units: List[ReferenceType["Unit"]] = []
        self._visible_cities: List[ReferenceType["City"]] = []
        self._visible_resources: List[ReferenceType["BaseResource"]] = []
        self._visible_improvements: List[ReferenceType["Improvement"]] = []
        self._visible_terrain: List[ReferenceType["BaseTerrain"]] = []

    def set_default_linger_turns(self, turns: int) -> None:
        self.default_linger_turns = max(0, turns)

    def get_default_linger_turns(self) -> int:
        return self.default_linger_turns

    def get_changed_tile_tags(self) -> Set[str]:
        return set(self._changed_tile_tags)

    def clear_changed_tile_tags(self) -> None:
        self._changed_tile_tags.clear()

    def get_tile_state(self, tile_or_tag: "Tile | str") -> VisionTileState:
        tile_tag = tile_or_tag.get_tag() if not isinstance(tile_or_tag, str) else tile_or_tag
        record = self._tile_records.get(tile_tag)
        if record is None:
            return VisionTileState.UNSEEN
        return record.state

    def get_turns_remaining(self, tile_or_tag: "Tile | str") -> int:
        tile_tag = tile_or_tag.get_tag() if not isinstance(tile_or_tag, str) else tile_or_tag
        record = self._tile_records.get(tile_tag)
        if record is None:
            return 0
        return record.turns_remaining

    def is_visible(self, tile_or_tag: "Tile | str") -> bool:
        tile_tag = tile_or_tag.get_tag() if not isinstance(tile_or_tag, str) else tile_or_tag
        record = self._tile_records.get(tile_tag)
        return record.is_visible if record is not None else False

    def is_explored(self, tile_or_tag: "Tile | str") -> bool:
        tile_tag = tile_or_tag.get_tag() if not isinstance(tile_or_tag, str) else tile_or_tag
        record = self._tile_records.get(tile_tag)
        return record.is_explored if record is not None else False

    def get_visible_tile_tags(self) -> Set[str]:
        return {tile_tag for tile_tag, record in self._tile_records.items() if record.is_visible}

    def get_explored_tile_tags(self) -> Set[str]:
        return {tile_tag for tile_tag, record in self._tile_records.items() if record.is_explored}

    def set_reveal_source(self, source_id: str, tiles_or_tags: Iterable["Tile | str"]) -> bool:
        next_tags: Set[str] = set()
        for tile_or_tag in tiles_or_tags:
            tile_tag = tile_or_tag.get_tag() if not isinstance(tile_or_tag, str) else tile_or_tag
            if tile_tag != "":
                next_tags.add(tile_tag)

        if not next_tags:
            return self.clear_reveal_source(source_id)

        previous = self._reveal_sources.get(source_id)
        if previous == next_tags:
            return False

        self._reveal_sources[source_id] = next_tags
        return True

    def clear_reveal_source(self, source_id: str) -> bool:
        return self._reveal_sources.pop(source_id, None) is not None

    def get_reveal_tile_tags(self) -> Set[str]:
        reveal_tags: Set[str] = set()
        for tile_tags in self._reveal_sources.values():
            reveal_tags.update(tile_tags)
        return reveal_tags

    def _remember_tile(self, tile: "Tile") -> None:
        self._tile_refs[tile.get_tag()] = ref(tile)

    def _resolve_tile_from_cache(self, tile_tag: str) -> "Tile | None":
        tile_ref = self._tile_refs.get(tile_tag)
        if tile_ref is None:
            return None
        return tile_ref()

    def _resolve_tile(self, tile_tag: str) -> "Tile | None":
        resolved = self._resolve_tile_from_cache(tile_tag)
        if resolved is not None:
            return resolved

        from managers.entity import EntityManager, EntityType

        tile_ref = cast(
            ReferenceType["Tile"] | None,
            EntityManager.get_singleton_instance().get_ref_weak(EntityType.TILE, tile_tag),
        )
        if tile_ref is None:
            return None

        tile = tile_ref()
        if tile is None:
            return None

        self._remember_tile(tile)
        return tile

    def _reset_runtime_views(self) -> None:
        self._visible_tiles = set()
        self._visible_units = []
        self._visible_cities = []
        self._visible_resources = []
        self._visible_improvements = []
        self._visible_terrain = []

    def _refresh_runtime_views(
        self,
        tiles: Iterable["Tile"],
        *,
        units: List["Unit"] | None = None,
        cities: List["City"] | None = None,
        resources: List["BaseResource"] | None = None,
        improvements: List["Improvement"] | None = None,
        terrain: List["BaseTerrain"] | None = None,
    ) -> None:
        self._reset_runtime_views()
        resolved_tiles = list(tiles)
        self._visible_tiles = {ref(tile) for tile in resolved_tiles}

        if units is None:
            unit_map: Dict[str, "Unit"] = {}
            for tile in resolved_tiles:
                for unit in tile.get_units():
                    unit_map[unit.get_tag()] = unit
            units = list(unit_map.values())

        if cities is None:
            city_map: Dict[str, "City"] = {}
            for tile in resolved_tiles:
                if tile.city is not None:
                    city_map[tile.city.get_tag()] = tile.city
            cities = list(city_map.values())

        if resources is None:
            visible_resources: List["BaseResource"] = []
            seen_resource_ids: Set[int] = set()
            for tile in resolved_tiles:
                for resource in tile.resources.flatten().values():
                    resource_id = id(resource)
                    if resource_id in seen_resource_ids:
                        continue
                    seen_resource_ids.add(resource_id)
                    visible_resources.append(resource)
            resources = visible_resources

        if improvements is None:
            visible_improvements: List["Improvement"] = []
            seen_improvement_ids: Set[int] = set()
            for tile in resolved_tiles:
                for improvement in tile.get_improvements():
                    improvement_id = id(improvement)
                    if improvement_id in seen_improvement_ids:
                        continue
                    seen_improvement_ids.add(improvement_id)
                    visible_improvements.append(improvement)
            improvements = visible_improvements

        if terrain is None:
            visible_terrain: List["BaseTerrain"] = []
            seen_terrain_ids: Set[int] = set()
            for tile in resolved_tiles:
                terrain_item = tile.get_terrain()
                terrain_id = id(terrain_item)
                if terrain_id in seen_terrain_ids:
                    continue
                seen_terrain_ids.add(terrain_id)
                visible_terrain.append(terrain_item)
            terrain = visible_terrain

        self._visible_units = [ref(unit) for unit in units]
        self._visible_cities = [ref(city) for city in cities]
        self._visible_resources = [ref(resource) for resource in resources]
        self._visible_improvements = [ref(improvement) for improvement in improvements]
        self._visible_terrain = [ref(terrain_item) for terrain_item in terrain]

    def recompute_visible_tiles(self, tiles: Set["Tile"], linger_turns: int | None = None) -> Set[str]:
        effective_linger_turns = self.default_linger_turns if linger_turns is None else max(0, linger_turns)

        visible_tile_tags: Set[str] = set()
        for tile in tiles:
            tile_tag = tile.get_tag()
            visible_tile_tags.add(tile_tag)
            self._remember_tile(tile)

        changed_tiles: Set[str] = set()
        all_tile_tags = set(self._tile_records.keys()) | visible_tile_tags

        for tile_tag in all_tile_tags:
            previous = self._tile_records.get(tile_tag)

            if tile_tag in visible_tile_tags:
                next_record = VisionTileRecord(
                    tile_tag=tile_tag,
                    state=VisionTileState.VISIBLE,
                    turns_remaining=effective_linger_turns,
                )
            elif previous is None:
                continue
            elif previous.state is VisionTileState.VISIBLE:
                if effective_linger_turns > 0:
                    next_record = VisionTileRecord(
                        tile_tag=tile_tag,
                        state=VisionTileState.LINGERING,
                        turns_remaining=effective_linger_turns,
                    )
                else:
                    next_record = VisionTileRecord(tile_tag=tile_tag, state=VisionTileState.FOGGED, turns_remaining=0)
            elif previous.state is VisionTileState.LINGERING:
                next_turns = max(0, previous.turns_remaining - 1)
                next_state = VisionTileState.LINGERING if next_turns > 0 else VisionTileState.FOGGED
                next_record = VisionTileRecord(tile_tag=tile_tag, state=next_state, turns_remaining=next_turns)
            else:
                next_record = VisionTileRecord(tile_tag=tile_tag, state=VisionTileState.FOGGED, turns_remaining=0)

            if previous != next_record:
                changed_tiles.add(tile_tag)

            self._tile_records[tile_tag] = next_record

        self._changed_tile_tags = changed_tiles
        self._refresh_runtime_views(self.get_visible_tiles())
        return changed_tiles

    def mass_set_visible_tiles(
        self,
        tiles: Set["Tile"] | None = None,
        units: List["Unit"] | None = None,
        cities: List["City"] | None = None,
        resources: List["BaseResource"] | None = None,
        improvements: List["Improvement"] | None = None,
        terrain: List["BaseTerrain"] | None = None,
    ) -> Set[str]:
        changed_tiles: Set[str] = set()
        if tiles is not None:
            changed_tiles = self.recompute_visible_tiles(tiles)

        if tiles is not None or any(item is not None for item in (units, cities, resources, improvements, terrain)):
            self._refresh_runtime_views(
                self.get_visible_tiles(),
                units=units,
                cities=cities,
                resources=resources,
                improvements=improvements,
                terrain=terrain,
            )

        return changed_tiles

    def get_visible_tiles(self) -> Set["Tile"]:
        tiles: Set["Tile"] = set()
        for tile_tag, record in self._tile_records.items():
            if not record.is_visible:
                continue

            resolved = self._resolve_tile(tile_tag)
            if resolved is not None:
                tiles.add(resolved)

        return tiles

    def add_visible_tile(self, tile: "Tile") -> None:
        self._remember_tile(tile)
        self._tile_records[tile.get_tag()] = VisionTileRecord(
            tile_tag=tile.get_tag(),
            state=VisionTileState.VISIBLE,
            turns_remaining=self.default_linger_turns,
        )
        self._refresh_runtime_views(self.get_visible_tiles())

    def remove_visible_tile(self, tile: "Tile") -> None:
        tile_tag = tile.get_tag()
        if tile_tag not in self._tile_records:
            return

        self._tile_records[tile_tag] = VisionTileRecord(tile_tag=tile_tag, state=VisionTileState.FOGGED, turns_remaining=0)
        self._refresh_runtime_views(self.get_visible_tiles())

    def get_visible_units(self) -> List["Unit"]:
        units: List["Unit"] = []
        for unit_ref in self._visible_units:
            if (resolved := unit_ref()) is not None:
                units.append(resolved)
        return units

    def add_visible_unit(self, unit: "Unit") -> None:
        unit_tags = {visible_unit.get_tag() for visible_unit in self.get_visible_units()}
        if unit.get_tag() not in unit_tags:
            self._visible_units.append(ref(unit))

    def remove_visible_unit(self, unit: "Unit") -> None:
        self._visible_units = [unit_ref for unit_ref in self._visible_units if (resolved := unit_ref()) is not None and resolved is not unit]

    def get_visible_cities(self) -> List["City"]:
        cities: List["City"] = []
        for city_ref in self._visible_cities:
            if (resolved := city_ref()) is not None:
                cities.append(resolved)
        return cities

    def add_visible_city(self, city: "City") -> None:
        city_tags = {visible_city.get_tag() for visible_city in self.get_visible_cities()}
        if city.get_tag() not in city_tags:
            self._visible_cities.append(ref(city))

    def remove_visible_city(self, city: "City") -> None:
        self._visible_cities = [city_ref for city_ref in self._visible_cities if (resolved := city_ref()) is not None and resolved is not city]

    def get_visible_resources(self) -> List["BaseResource"]:
        resources: List["BaseResource"] = []
        for resource_ref in self._visible_resources:
            if (resolved := resource_ref()) is not None:
                resources.append(resolved)
        return resources

    def add_visible_resource(self, resource: "BaseResource") -> None:
        resource_ids = {id(visible_resource) for visible_resource in self.get_visible_resources()}
        if id(resource) not in resource_ids:
            self._visible_resources.append(ref(resource))

    def remove_visible_resource(self, resource: "BaseResource") -> None:
        self._visible_resources = [
            resource_ref for resource_ref in self._visible_resources if (resolved := resource_ref()) is not None and resolved is not resource
        ]

    def get_visible_improvements(self) -> List["Improvement"]:
        improvements: List["Improvement"] = []
        for improvement_ref in self._visible_improvements:
            if (resolved := improvement_ref()) is not None:
                improvements.append(resolved)
        return improvements

    def add_visible_improvement(self, improvement: "Improvement") -> None:
        improvement_ids = {id(visible_improvement) for visible_improvement in self.get_visible_improvements()}
        if id(improvement) not in improvement_ids:
            self._visible_improvements.append(ref(improvement))

    def remove_visible_improvement(self, improvement: "Improvement") -> None:
        self._visible_improvements = [
            improvement_ref
            for improvement_ref in self._visible_improvements
            if (resolved := improvement_ref()) is not None and resolved is not improvement
        ]

    def get_visible_terrain(self) -> List["BaseTerrain"]:
        terrain: List["BaseTerrain"] = []
        for terrain_ref in self._visible_terrain:
            if (resolved := terrain_ref()) is not None:
                terrain.append(resolved)
        return terrain

    def add_visible_terrain(self, terrain: "BaseTerrain") -> None:
        terrain_ids = {id(visible_terrain) for visible_terrain in self.get_visible_terrain()}
        if id(terrain) not in terrain_ids:
            self._visible_terrain.append(ref(terrain))

    def remove_visible_terrain(self, terrain: "BaseTerrain") -> None:
        self._visible_terrain = [
            terrain_ref for terrain_ref in self._visible_terrain if (resolved := terrain_ref()) is not None and resolved is not terrain
        ]

    def dump(self) -> Dict[str, Any]:
        return {
            "linger_turns": self.default_linger_turns,
            "tiles": [self._tile_records[tile_tag].dump() for tile_tag in sorted(self._tile_records.keys())],
        }

    def load_state(self, state: Dict[str, Any] | List[str]) -> None:
        self._tile_records = {}
        self._tile_refs = {}
        self._reveal_sources = {}
        self._changed_tile_tags = set()
        self._reset_runtime_views()

        if isinstance(state, list):
            for tile_tag in state:
                self._tile_records[tile_tag] = VisionTileRecord(
                    tile_tag=tile_tag,
                    state=VisionTileState.VISIBLE,
                    turns_remaining=self.default_linger_turns,
                )
        else:
            self.default_linger_turns = max(0, int(state.get("linger_turns", self.default_linger_turns)))
            for record_data in cast(List[Dict[str, Any]], state.get("tiles", [])):
                record = VisionTileRecord.from_dict(record_data)
                if record.tile_tag == "":
                    continue
                self._tile_records[record.tile_tag] = record

        self._refresh_runtime_views(self.get_visible_tiles())

    def resolve_ref(self, refs: List[ReferenceType[Any]]) -> List[Any]:
        resolved: List[Any] = []
        for ref_item in refs:
            if (resolved_item := ref_item()) is not None:
                resolved.append(resolved_item)
        return resolved
