from dataclasses import dataclass
from enum import Enum
import logging
from time import perf_counter
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Literal, Protocol, Set, Tuple, TypeAlias, TypeVar, cast
from weakref import ReferenceType, ref

if TYPE_CHECKING:
    from gameplay.city import City
    from gameplay.improvement import Improvement
    from gameplay.resource import BaseResource
    from gameplay.terrain._base_terrain import BaseTerrain
    from gameplay.tile import Tile
    from gameplay.unit import Unit


T = TypeVar("T")


HexOffsetLayout: TypeAlias = Literal["odd-q", "even-q"]
OffsetCoord: TypeAlias = Tuple[int, int]
CubeCoord: TypeAlias = Tuple[int, int, int]


VISION_TIMING_LOGGER = logging.getLogger("sciv.timing.vision")
VISION_TIMING_LOG_LEVEL = logging.INFO


@dataclass(slots=True)
class VisionTimingSample:
    label: str
    started_at: float
    enabled: bool

    @classmethod
    def start(cls, label: str) -> "VisionTimingSample":
        enabled = VISION_TIMING_LOGGER.isEnabledFor(VISION_TIMING_LOG_LEVEL)
        return cls(label=label, started_at=perf_counter() if enabled else 0.0, enabled=enabled)

    def finish(self, **details: object) -> None:
        if not self.enabled:
            return

        elapsed_ms = (perf_counter() - self.started_at) * 1000.0
        detail_text = ""
        if details:
            detail_text = " " + " ".join(f"{key}={value}" for key, value in details.items())

        VISION_TIMING_LOGGER.log(VISION_TIMING_LOG_LEVEL, "vision.%s elapsed_ms=%.3f%s", self.label, elapsed_ms, detail_text)


class RadiusTileLike(Protocol):
    x: int
    y: int

    def get_tag(self) -> str: ...



@dataclass(slots=True)
class HexVisionRadiusIndex:
    tiles_by_coord: Dict[OffsetCoord, RadiusTileLike]
    layout: HexOffsetLayout = "odd-q"

    @classmethod
    def build(cls, tiles: Iterable[RadiusTileLike], *, layout: HexOffsetLayout = "odd-q") -> "HexVisionRadiusIndex":
        timing = VisionTimingSample.start("radius_index.build")
        indexed_tiles: Dict[OffsetCoord, RadiusTileLike] = {}

        for tile in tiles:
            indexed_tiles[(int(tile.x), int(tile.y))] = tile

        timing.finish(tile_count=len(indexed_tiles), layout=layout)
        return cls(tiles_by_coord=indexed_tiles, layout=layout)

    def refresh_tile(self, tile: RadiusTileLike) -> None:
        self.tiles_by_coord[(int(tile.x), int(tile.y))] = tile

    def tiles_in_radius(self, origin: RadiusTileLike, radius: int) -> Set[RadiusTileLike]:
        timing = VisionTimingSample.start("radius_index.tiles_in_radius")
        resolved_tiles: Set[RadiusTileLike] = set()
        clamped_radius = max(0, radius)

        for coord in self.coords_in_radius(int(origin.x), int(origin.y), clamped_radius):
            tile = self.tiles_by_coord.get(coord)
            if tile is not None:
                resolved_tiles.add(tile)

        timing.finish(radius=clamped_radius, resolved_tile_count=len(resolved_tiles))
        return resolved_tiles

    def tile_tags_in_radius(self, origin: RadiusTileLike, radius: int) -> Set[str]:
        return {tile.get_tag() for tile in self.tiles_in_radius(origin, radius)}

    def coords_in_radius(self, col: int, row: int, radius: int) -> Set[OffsetCoord]:
        timing = VisionTimingSample.start("radius_index.coords_in_radius")
        clamped_radius = max(0, radius)
        center = self._offset_to_cube(col, row)
        coords: Set[OffsetCoord] = set()

        for dx in range(-clamped_radius, clamped_radius + 1):
            min_dy = max(-clamped_radius, -dx - clamped_radius)
            max_dy = min(clamped_radius, -dx + clamped_radius)

            for dy in range(min_dy, max_dy + 1):
                dz = -dx - dy
                cube = (center[0] + dx, center[1] + dy, center[2] + dz)
                coords.add(self._cube_to_offset(cube))

        timing.finish(col=col, row=row, radius=clamped_radius, coord_count=len(coords))
        return coords

    def _offset_to_cube(self, col: int, row: int) -> CubeCoord:
        x = col

        if self.layout == "odd-q":
            z = row - (col - (col & 1)) // 2
        else:
            z = row - (col + (col & 1)) // 2

        y = -x - z
        return x, y, z

    def _cube_to_offset(self, cube: CubeCoord) -> OffsetCoord:
        x, _, z = cube
        col = x

        if self.layout == "odd-q":
            row = z + (x - (x & 1)) // 2
        else:
            row = z + (x + (x & 1)) // 2

        return col, row


class VisionTileLike(Protocol):
    def get_tag(self) -> str: ...


def collect_radius_visibility(origin: T, radius: int, neighbor_getter: Callable[[T, int], Iterable[T]]) -> Set[T]:
    timing = VisionTimingSample.start("visibility.collect_radius")
    visible_tiles: Set[T] = {origin}

    if radius <= 0:
        timing.finish(radius=radius, visible_tile_count=len(visible_tiles))
        return visible_tiles

    visible_tiles.update(neighbor_getter(origin, radius))
    timing.finish(radius=radius, visible_tile_count=len(visible_tiles))
    return visible_tiles


def expand_border_visibility(core_tiles: Iterable[T], border_radius: int, neighbor_getter: Callable[[T], Iterable[T]]) -> Set[T]:
    timing = VisionTimingSample.start("visibility.expand_border")
    visible_tiles: Set[T] = set(core_tiles)
    frontier: Set[T] = set(visible_tiles)
    iterations = 0

    if border_radius <= 0:
        timing.finish(border_radius=border_radius, iterations=iterations, visible_tile_count=len(visible_tiles))
        return visible_tiles

    for _ in range(border_radius):
        iterations += 1
        next_frontier: Set[T] = set()
        for tile in frontier:
            next_frontier.update(neighbor_getter(tile))

        next_frontier -= visible_tiles
        if not next_frontier:
            break

        visible_tiles.update(next_frontier)
        frontier = next_frontier

    timing.finish(border_radius=border_radius, iterations=iterations, visible_tile_count=len(visible_tiles))
    return visible_tiles


class VisionTileState(str, Enum):
    UNSEEN = "unseen"
    VISIBLE = "visible"
    LINGERING = "lingering"
    FOGGED = "fogged"


def is_visible_for_render(state: VisionTileState) -> bool:
    return state in {VisionTileState.VISIBLE, VisionTileState.LINGERING}


def build_tile_visibility_states(vision: "Vision", tiles: Iterable[VisionTileLike]) -> Dict[str, VisionTileState]:
    timing = VisionTimingSample.start("visibility.build_tile_states")
    visibility_states: Dict[str, VisionTileState] = {}

    for tile in tiles:
        tile_tag = tile.get_tag()
        visibility_states[tile_tag] = vision.get_tile_state(tile_tag)

    timing.finish(tile_count=len(visibility_states))
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
        self._direct_visible_tile_tags: Set[str] = set()
        self._render_visible_tile_tags: Set[str] = set()
        self._explored_tile_tags: Set[str] = set()
        self._lingering_tile_tags: Set[str] = set()
        self._runtime_views_dirty: bool = True
        self._source_ref_counts: Dict[str, int] = {}
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
        return tile_tag in self._render_visible_tile_tags

    def is_explored(self, tile_or_tag: "Tile | str") -> bool:
        tile_tag = tile_or_tag.get_tag() if not isinstance(tile_or_tag, str) else tile_or_tag
        return tile_tag in self._explored_tile_tags

    def get_visible_tile_tags(self) -> Set[str]:
        return set(self._render_visible_tile_tags)

    def get_explored_tile_tags(self) -> Set[str]:
        return set(self._explored_tile_tags)

    def get_visible_tile_count(self) -> int:
        return len(self._render_visible_tile_tags)

    def get_explored_tile_count(self) -> int:
        return len(self._explored_tile_tags)

    def mark_runtime_views_dirty(self) -> None:
        self._runtime_views_dirty = True

    def update_reveal_source_tiles(self, source_id: str, tiles_or_tags: Iterable[object]) -> Set[str]:
        timing = VisionTimingSample.start("reveal_source.update")
        next_tags: Set[str] = set()

        for tile_or_tag in tiles_or_tags:
            if isinstance(tile_or_tag, str):
                tile_tag = tile_or_tag
            else:
                get_tag = getattr(tile_or_tag, "get_tag", None)
                if not callable(get_tag):
                    continue
                tile_tag = str(get_tag())
                self._tile_refs[tile_tag] = ref(cast("Tile", tile_or_tag))

            if tile_tag != "":
                next_tags.add(tile_tag)

        previous_tags = self._reveal_sources.get(source_id, set())
        if previous_tags == next_tags:
            self._changed_tile_tags = set()
            timing.finish(
                source_id=source_id,
                previous_tile_count=len(previous_tags),
                next_tile_count=len(next_tags),
                added_tile_count=0,
                removed_tile_count=0,
                changed_tile_count=0,
                skipped=True,
            )
            return set()

        removed_tags = previous_tags - next_tags
        added_tags = next_tags - previous_tags
        changed_tags: Set[str] = set()

        if next_tags:
            self._reveal_sources[source_id] = next_tags
        else:
            self._reveal_sources.pop(source_id, None)

        for tile_tag in removed_tags:
            next_count = self._source_ref_counts.get(tile_tag, 0) - 1

            if next_count > 0:
                self._source_ref_counts[tile_tag] = next_count
                continue

            self._source_ref_counts.pop(tile_tag, None)
            next_state = VisionTileState.LINGERING if self.default_linger_turns > 0 else VisionTileState.FOGGED
            next_turns = self.default_linger_turns if next_state is VisionTileState.LINGERING else 0

            if self._set_incremental_tile_state(tile_tag, next_state, next_turns):
                changed_tags.add(tile_tag)

        for tile_tag in added_tags:
            self._source_ref_counts[tile_tag] = self._source_ref_counts.get(tile_tag, 0) + 1

            if self._set_incremental_tile_state(tile_tag, VisionTileState.VISIBLE, self.default_linger_turns):
                changed_tags.add(tile_tag)

        self._changed_tile_tags = changed_tags
        timing.finish(
            source_id=source_id,
            previous_tile_count=len(previous_tags),
            next_tile_count=len(next_tags),
            added_tile_count=len(added_tags),
            removed_tile_count=len(removed_tags),
            changed_tile_count=len(changed_tags),
            reveal_source_count=len(self._reveal_sources),
        )
        return changed_tags

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
        previous_tags = self._reveal_sources.get(source_id, set())
        changed_tags = self.update_reveal_source_tiles(source_id, ())
        return bool(previous_tags or changed_tags)

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
        self._runtime_views_dirty = False

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
        timing = VisionTimingSample.start("runtime_views.refresh")
        self._reset_runtime_views()

        resolve_tiles_timing = VisionTimingSample.start("runtime_views.resolve_tiles")
        resolved_tiles = list(tiles)
        self._visible_tiles = {ref(tile) for tile in resolved_tiles}
        resolve_tiles_timing.finish(tile_count=len(resolved_tiles))

        if units is None:
            collect_units_timing = VisionTimingSample.start("runtime_views.collect_units")
            unit_map: Dict[str, "Unit"] = {}
            for tile in resolved_tiles:
                for unit in tile.get_units():
                    unit_map[unit.get_tag()] = unit
            units = list(unit_map.values())
            collect_units_timing.finish(tile_count=len(resolved_tiles), unit_count=len(units))

        if cities is None:
            collect_cities_timing = VisionTimingSample.start("runtime_views.collect_cities")
            city_map: Dict[str, "City"] = {}
            for tile in resolved_tiles:
                if tile.city is not None:
                    city_map[tile.city.get_tag()] = tile.city
            cities = list(city_map.values())
            collect_cities_timing.finish(tile_count=len(resolved_tiles), city_count=len(cities))

        if resources is None:
            collect_resources_timing = VisionTimingSample.start("runtime_views.collect_resources")
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
            collect_resources_timing.finish(tile_count=len(resolved_tiles), resource_count=len(resources))

        if improvements is None:
            collect_improvements_timing = VisionTimingSample.start("runtime_views.collect_improvements")
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
            collect_improvements_timing.finish(tile_count=len(resolved_tiles), improvement_count=len(improvements))

        if terrain is None:
            collect_terrain_timing = VisionTimingSample.start("runtime_views.collect_terrain")
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
            collect_terrain_timing.finish(tile_count=len(resolved_tiles), terrain_count=len(terrain))

        sync_refs_timing = VisionTimingSample.start("runtime_views.sync_refs")
        self._visible_units = [ref(unit) for unit in units]
        self._visible_cities = [ref(city) for city in cities]
        self._visible_resources = [ref(resource) for resource in resources]
        self._visible_improvements = [ref(improvement) for improvement in improvements]
        self._visible_terrain = [ref(terrain_item) for terrain_item in terrain]
        self._runtime_views_dirty = False
        sync_refs_timing.finish(
            unit_count=len(units),
            city_count=len(cities),
            resource_count=len(resources),
            improvement_count=len(improvements),
            terrain_count=len(terrain),
        )
        timing.finish(
            tile_count=len(resolved_tiles),
            unit_count=len(units),
            city_count=len(cities),
            resource_count=len(resources),
            improvement_count=len(improvements),
            terrain_count=len(terrain),
        )

    def _ensure_runtime_views(self) -> None:
        if not self._runtime_views_dirty:
            return

        self._refresh_runtime_views(self.get_visible_tiles())

    def _sync_indexes_from_records(self) -> None:
        self._direct_visible_tile_tags = set()
        self._render_visible_tile_tags = set()
        self._explored_tile_tags = set()
        self._lingering_tile_tags = set()

        for tile_tag, record in self._tile_records.items():
            self._index_record(tile_tag, record)

    def _index_record(self, tile_tag: str, record: VisionTileRecord) -> None:
        if record.state is VisionTileState.VISIBLE:
            self._direct_visible_tile_tags.add(tile_tag)
        else:
            self._direct_visible_tile_tags.discard(tile_tag)

        if record.state is VisionTileState.LINGERING:
            self._lingering_tile_tags.add(tile_tag)
        else:
            self._lingering_tile_tags.discard(tile_tag)

        if record.is_visible:
            self._render_visible_tile_tags.add(tile_tag)
        else:
            self._render_visible_tile_tags.discard(tile_tag)

        if record.is_explored:
            self._explored_tile_tags.add(tile_tag)
        else:
            self._explored_tile_tags.discard(tile_tag)

    def _store_tile_record(self, record: VisionTileRecord, changed_tiles: Set[str]) -> None:
        previous = self._tile_records.get(record.tile_tag)
        if previous == record:
            return

        self._tile_records[record.tile_tag] = record
        self._index_record(record.tile_tag, record)
        changed_tiles.add(record.tile_tag)

    def advance_lingering_tiles(self) -> Set[str]:
        timing = VisionTimingSample.start("visible_tiles.advance_lingering")
        changed_tags: Set[str] = set()
        initial_lingering_count = len(self._lingering_tile_tags)

        for tile_tag in list(self._lingering_tile_tags):
            if self._source_ref_counts.get(tile_tag, 0) > 0:
                self._lingering_tile_tags.discard(tile_tag)
                continue

            record = self._tile_records.get(tile_tag)
            if record is None or record.state is not VisionTileState.LINGERING:
                self._lingering_tile_tags.discard(tile_tag)
                continue

            turns_remaining = max(0, record.turns_remaining - 1)
            next_state = VisionTileState.LINGERING if turns_remaining > 0 else VisionTileState.FOGGED

            if self._set_incremental_tile_state(tile_tag, next_state, turns_remaining):
                changed_tags.add(tile_tag)

        self._changed_tile_tags = changed_tags
        timing.finish(
            initial_lingering_tile_count=initial_lingering_count,
            remaining_lingering_tile_count=len(self._lingering_tile_tags),
            changed_tile_count=len(changed_tags),
        )
        return changed_tags

    def _set_incremental_tile_state(self, tile_tag: str, state: VisionTileState, turns_remaining: int) -> bool:
        previous_record = self._tile_records.get(tile_tag)
        previous_state = previous_record.state if previous_record is not None else VisionTileState.UNSEEN
        next_record = VisionTileRecord(tile_tag=tile_tag, state=state, turns_remaining=max(0, turns_remaining))

        if previous_record == next_record:
            return False

        self._tile_records[tile_tag] = next_record
        self._sync_incremental_tile_caches(tile_tag, state)
        self._runtime_views_dirty = True

        return previous_state is not state

    def _sync_incremental_tile_caches(self, tile_tag: str, state: VisionTileState) -> None:
        if state is VisionTileState.VISIBLE:
            self._direct_visible_tile_tags.add(tile_tag)
            self._render_visible_tile_tags.add(tile_tag)
            self._explored_tile_tags.add(tile_tag)
            self._lingering_tile_tags.discard(tile_tag)
            return

        self._direct_visible_tile_tags.discard(tile_tag)

        if state is VisionTileState.LINGERING:
            self._render_visible_tile_tags.add(tile_tag)
            self._explored_tile_tags.add(tile_tag)
            self._lingering_tile_tags.add(tile_tag)
            return

        self._render_visible_tile_tags.discard(tile_tag)
        self._lingering_tile_tags.discard(tile_tag)

        if state is VisionTileState.FOGGED:
            self._explored_tile_tags.add(tile_tag)
            return

        self._explored_tile_tags.discard(tile_tag)

    def _rebuild_incremental_tile_caches(self) -> None:
        self._direct_visible_tile_tags.clear()
        self._render_visible_tile_tags.clear()
        self._explored_tile_tags.clear()
        self._lingering_tile_tags.clear()

        for tile_tag, record in self._tile_records.items():
            self._sync_incremental_tile_caches(tile_tag, record.state)

    def _ensure_runtime_views_current(self) -> None:
        if not self._runtime_views_dirty:
            return

        self._refresh_runtime_views(self.get_visible_tiles())
        self._runtime_views_dirty = False

    def recompute_visible_tiles(
        self,
        tiles: Set["Tile"],
        linger_turns: int | None = None,
        *,
        advance_linger: bool = True,
    ) -> Set[str]:
        timing = VisionTimingSample.start("visible_tiles.recompute")
        effective_linger_turns = self.default_linger_turns if linger_turns is None else max(0, linger_turns)

        next_direct_visible_tags: Set[str] = set()
        for tile in tiles:
            tile_tag = tile.get_tag()
            if tile_tag == "":
                continue
            next_direct_visible_tags.add(tile_tag)
            self._remember_tile(tile)

        previous_direct_visible_tags = set(self._direct_visible_tile_tags)
        lost_direct_visible_tags = previous_direct_visible_tags - next_direct_visible_tags
        lingering_tags: Set[str] = self._lingering_tile_tags - next_direct_visible_tags if advance_linger else set()
        changed_tiles: Set[str] = set()

        for tile_tag in next_direct_visible_tags:
            self._store_tile_record(
                VisionTileRecord(
                    tile_tag=tile_tag,
                    state=VisionTileState.VISIBLE,
                    turns_remaining=effective_linger_turns,
                ),
                changed_tiles,
            )

        for tile_tag in lost_direct_visible_tags:
            if effective_linger_turns > 0:
                next_record = VisionTileRecord(
                    tile_tag=tile_tag,
                    state=VisionTileState.LINGERING,
                    turns_remaining=effective_linger_turns,
                )
            else:
                next_record = VisionTileRecord(tile_tag=tile_tag, state=VisionTileState.FOGGED, turns_remaining=0)

            self._store_tile_record(next_record, changed_tiles)

        for tile_tag in lingering_tags:
            previous = self._tile_records.get(tile_tag)
            if previous is None or previous.state is not VisionTileState.LINGERING:
                continue

            next_turns = max(0, previous.turns_remaining - 1)
            next_state = VisionTileState.LINGERING if next_turns > 0 else VisionTileState.FOGGED
            self._store_tile_record(
                VisionTileRecord(tile_tag=tile_tag, state=next_state, turns_remaining=next_turns),
                changed_tiles,
            )

        self._changed_tile_tags = changed_tiles
        self._direct_visible_tile_tags = next_direct_visible_tags
        self._runtime_views_dirty = True
        timing.finish(
            input_tile_count=len(tiles),
            previous_direct_visible_tile_count=len(previous_direct_visible_tags),
            next_direct_visible_tile_count=len(next_direct_visible_tags),
            lost_direct_visible_tile_count=len(lost_direct_visible_tags),
            lingering_tile_count=len(lingering_tags),
            changed_tile_count=len(changed_tiles),
            advance_linger=advance_linger,
        )
        return changed_tiles

    def mass_set_visible_tiles(
        self,
        tiles: Set["Tile"] | None = None,
        units: List["Unit"] | None = None,
        cities: List["City"] | None = None,
        resources: List["BaseResource"] | None = None,
        improvements: List["Improvement"] | None = None,
        terrain: List["BaseTerrain"] | None = None,
        *,
        advance_linger: bool = True,
    ) -> Set[str]:
        timing = VisionTimingSample.start("visible_tiles.mass_set")
        changed_tiles: Set[str] = set()
        explicit_runtime_views = any(item is not None for item in (units, cities, resources, improvements, terrain))

        if tiles is not None:
            changed_tiles = self.recompute_visible_tiles(tiles, advance_linger=advance_linger)

        if explicit_runtime_views:
            self._refresh_runtime_views(
                self.get_visible_tiles(),
                units=units,
                cities=cities,
                resources=resources,
                improvements=improvements,
                terrain=terrain,
            )

        timing.finish(
            input_tile_count=len(tiles) if tiles is not None else 0,
            changed_tile_count=len(changed_tiles),
            explicit_runtime_views=explicit_runtime_views,
            unit_count=len(units) if units is not None else 0,
            city_count=len(cities) if cities is not None else 0,
            resource_count=len(resources) if resources is not None else 0,
            improvement_count=len(improvements) if improvements is not None else 0,
            terrain_count=len(terrain) if terrain is not None else 0,
            advance_linger=advance_linger,
        )
        return changed_tiles

    def get_visible_tiles(self) -> Set["Tile"]:
        timing = VisionTimingSample.start("visible_tiles.resolve")
        tiles: Set["Tile"] = set()
        cache_hit_count = 0
        entity_lookup_count = 0

        for tile_tag in self._render_visible_tile_tags:
            resolved = self._resolve_tile_from_cache(tile_tag)
            if resolved is not None:
                cache_hit_count += 1
            else:
                entity_lookup_count += 1
                resolved = self._resolve_tile(tile_tag)

            if resolved is not None:
                tiles.add(resolved)

        timing.finish(
            render_visible_tile_count=len(self._render_visible_tile_tags),
            resolved_tile_count=len(tiles),
            cache_hit_count=cache_hit_count,
            entity_lookup_count=entity_lookup_count,
        )
        return tiles

    def add_visible_tile(self, tile: "Tile") -> None:
        self._remember_tile(tile)
        changed_tiles: Set[str] = set()
        self._store_tile_record(
            VisionTileRecord(
                tile_tag=tile.get_tag(),
                state=VisionTileState.VISIBLE,
                turns_remaining=self.default_linger_turns,
            ),
            changed_tiles,
        )
        self._changed_tile_tags = changed_tiles
        self._runtime_views_dirty = True

    def remove_visible_tile(self, tile: "Tile") -> None:
        tile_tag = tile.get_tag()
        if tile_tag not in self._tile_records:
            return

        changed_tiles: Set[str] = set()
        self._store_tile_record(
            VisionTileRecord(tile_tag=tile_tag, state=VisionTileState.FOGGED, turns_remaining=0),
            changed_tiles,
        )
        self._changed_tile_tags = changed_tiles
        self._runtime_views_dirty = True

    def get_visible_units(self) -> List["Unit"]:
        self._ensure_runtime_views()
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
        self._ensure_runtime_views()
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
        self._ensure_runtime_views()
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
        self._ensure_runtime_views()
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
        self._ensure_runtime_views()
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
        timing = VisionTimingSample.start("vision.load_state")
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

        self._sync_indexes_from_records()
        self._runtime_views_dirty = True
        timing.finish(
            record_count=len(self._tile_records),
            direct_visible_tile_count=len(self._direct_visible_tile_tags),
            render_visible_tile_count=len(self._render_visible_tile_tags),
            explored_tile_count=len(self._explored_tile_tags),
            lingering_tile_count=len(self._lingering_tile_tags),
        )

    def resolve_ref(self, refs: List[ReferenceType[Any]]) -> List[Any]:
        resolved: List[Any] = []
        for ref_item in refs:
            if (resolved_item := ref_item()) is not None:
                resolved.append(resolved_item)
        return resolved
