from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Dict, List, Sequence, Tuple, cast

from gameplay.repositories.tile import TileRepository
from helpers.cache import Cache
from system.subsystems.hexgen.enums import GeoformType, HexFeature

if TYPE_CHECKING:
    from gameplay.tile import Tile


@dataclass(frozen=True, slots=True)
class TileScoringProfile:
    food_weight: float = 2.0
    production_weight: float = 1.8
    gold_weight: float = 0.6
    science_weight: float = 0.5
    culture_weight: float = 0.4
    housing_weight: float = 0.3

    immediate_ring_weight: float = 1.0
    nearby_ring_weight: float = 0.45

    coast_bonus: float = 4.0
    no_coast_penalty: float = -1.5
    river_bonus: float = 3.5
    freshwater_bonus: float = 1.5

    hill_bonus: float = 0.7
    mountain_penalty: float = 1.1
    deep_water_penalty: float = 0.9

    resource_bonus_scale: float = 1.25
    resource_bonus_cap: float = 2.5
    expansion_bonus: float = 0.25
    edge_penalty: float = 2.5

    peninsula_bonus: float = 0.75
    isthmus_bonus: float = 0.8
    bay_bonus: float = 0.5
    strait_bonus: float = 0.4
    island_bonus: float = 0.9

    coast_bonus_scale: float = 1.0
    water_penalty_scale: float = 1.0
    expansion_bonus_scale: float = 1.0
    edge_penalty_scale: float = 1.0


DEFAULT_TILE_SCORING_PROFILE = TileScoringProfile()


def get_active_map_script() -> str | None:
    try:
        settings = Cache.get_game_settings()
    except AssertionError:
        return None

    raw_options: object = getattr(settings, "generator_options", {})
    if not isinstance(raw_options, dict):
        return None

    generator_options = cast(dict[str, object], raw_options)
    raw_map_script = generator_options.get("map_script")
    return raw_map_script if isinstance(raw_map_script, str) else None


def resolve_tile_scoring_profile(map_script: str | None = None) -> TileScoringProfile:
    script = map_script or get_active_map_script()
    profile = DEFAULT_TILE_SCORING_PROFILE

    if script == "archipelago":
        return replace(
            profile,
            coast_bonus=6.5,
            no_coast_penalty=-0.25,
            coast_bonus_scale=1.15,
            water_penalty_scale=0.45,
            expansion_bonus_scale=0.8,
            island_bonus=1.4,
            bay_bonus=0.8,
            strait_bonus=0.75,
        )

    if script == "pangaea":
        return replace(
            profile,
            coast_bonus=2.4,
            no_coast_penalty=-0.3,
            coast_bonus_scale=0.65,
            water_penalty_scale=1.1,
            expansion_bonus_scale=1.35,
            edge_penalty_scale=1.15,
        )

    if script == "small_continents":
        return replace(
            profile,
            coast_bonus=5.2,
            no_coast_penalty=-0.8,
            coast_bonus_scale=1.05,
            water_penalty_scale=0.7,
            island_bonus=1.15,
        )

    if script == "fractal":
        return replace(
            profile,
            bay_bonus=0.9,
            strait_bonus=0.9,
            peninsula_bonus=1.0,
            coast_bonus=4.8,
            water_penalty_scale=0.75,
        )

    return profile


def score_tile(
    tile: "Tile",
    profile: TileScoringProfile | None = None,
    map_dimensions: Tuple[int, int] | None = None,
    allow_edge_bias: bool = False,
    tile_yield_score_cache: Dict[Tuple[int, int], float] | None = None,
    neighbor_cache: Dict[Tuple[int, int], List["Tile"]] | None = None,
) -> float:
    resolved_profile = profile or resolve_tile_scoring_profile()
    resolved_dimensions = map_dimensions or _get_map_dimensions()

    tile.calculate()

    immediate_ring = _get_cached_neighbors(tile, 1, neighbor_cache)
    nearby_ring = _get_cached_neighbors(tile, 2, neighbor_cache)

    immediate_score = _yield_score(
        [tile, *immediate_ring],
        resolved_profile.immediate_ring_weight,
        resolved_profile,
        tile_yield_score_cache,
    )
    nearby_score = _yield_score(
        nearby_ring,
        resolved_profile.nearby_ring_weight,
        resolved_profile,
        tile_yield_score_cache,
    )

    coast_bonus = (
        resolved_profile.coast_bonus * resolved_profile.coast_bonus_scale
        if _has_coastal_access(tile)
        else resolved_profile.no_coast_penalty
    )
    river_bonus = resolved_profile.river_bonus if _has_river_edge(tile) else 0.0
    freshwater_bonus = resolved_profile.freshwater_bonus if any(_has_river_edge(neighbor) for neighbor in immediate_ring) else 0.0

    hills_bonus = sum(resolved_profile.hill_bonus for neighbor in immediate_ring if 170 <= neighbor.altitude < 217)
    mountain_penalty = sum(resolved_profile.mountain_penalty for neighbor in immediate_ring if neighbor.altitude >= 217)
    water_penalty = sum(
        resolved_profile.deep_water_penalty * resolved_profile.water_penalty_scale
        for neighbor in immediate_ring
        if neighbor.is_water and not neighbor.is_coast
    )

    resource_bonus = 0.0
    for neighbor in [tile, *nearby_ring]:
        resource_count = len(neighbor.resources.flatten_non_mechanic())
        resource_bonus += min(resolved_profile.resource_bonus_cap, float(resource_count) * resolved_profile.resource_bonus_scale)

    expansion_score = sum(
        resolved_profile.expansion_bonus * resolved_profile.expansion_bonus_scale
        for neighbor in nearby_ring
        if neighbor.is_passable() and not neighbor.is_water
    )

    feature_bonus = 0.0
    feature_bonus += resolved_profile.peninsula_bonus if _has_feature(tile, HexFeature.peninsula) else 0.0
    feature_bonus += resolved_profile.isthmus_bonus if _has_feature(tile, HexFeature.isthmus) else 0.0
    feature_bonus += resolved_profile.bay_bonus if any(_has_feature(neighbor, HexFeature.bay) for neighbor in immediate_ring) else 0.0
    feature_bonus += resolved_profile.strait_bonus if any(_has_feature(neighbor, HexFeature.strait) for neighbor in immediate_ring) else 0.0
    feature_bonus += (
        resolved_profile.island_bonus
        if _matches_geoform(tile, GeoformType.small_island, GeoformType.large_island, GeoformType.peninsula)
        else 0.0
    )

    edge_penalty = 0.0
    if resolved_dimensions != (0, 0) and TileRepository.is_near_map_edge(resolved_dimensions, tile, threshold=4):
        edge_penalty = resolved_profile.edge_penalty * resolved_profile.edge_penalty_scale
        if allow_edge_bias:
            edge_penalty *= 0.4

    return (
        immediate_score
        + nearby_score
        + coast_bonus
        + river_bonus
        + freshwater_bonus
        + hills_bonus
        + resource_bonus
        + expansion_score
        + feature_bonus
        - mountain_penalty
        - water_penalty
        - edge_penalty
    )


def rank_tiles(
    tiles: Sequence["Tile"],
    profile: TileScoringProfile | None = None,
    map_dimensions: Tuple[int, int] | None = None,
    allow_edge_bias: bool = False,
    limit: int | None = None,
) -> list[tuple["Tile", float]]:
    resolved_profile = profile or resolve_tile_scoring_profile()
    resolved_dimensions = map_dimensions or _get_map_dimensions()
    tile_yield_score_cache: Dict[Tuple[int, int], float] = {}
    neighbor_cache: Dict[Tuple[int, int], List["Tile"]] = {}

    ranked = [
        (
            tile,
            score_tile(
                tile,
                profile=resolved_profile,
                map_dimensions=resolved_dimensions,
                allow_edge_bias=allow_edge_bias,
                tile_yield_score_cache=tile_yield_score_cache,
                neighbor_cache=neighbor_cache,
            ),
        )
        for tile in tiles
    ]
    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked if limit is None else ranked[:limit]


def _yield_score(
    tiles: Sequence["Tile"],
    weight: float,
    profile: TileScoringProfile,
    tile_yield_score_cache: Dict[Tuple[int, int], float] | None = None,
) -> float:
    total = 0.0
    for tile in tiles:
        total += _weighted_tile_yield_score(tile, profile, tile_yield_score_cache) * weight
    return total


def _get_map_dimensions() -> tuple[int, int]:
    try:
        settings = Cache.get_game_settings()
    except AssertionError:
        return (0, 0)
    return (int(settings.width), int(settings.height))


def _has_coastal_access(tile: "Tile") -> bool:
    if tile.is_coast:
        return True
    return any(neighbor.is_water and neighbor.is_coast for neighbor in TileRepository.get_neighbors(tile, radius=1))


def _has_river_edge(tile: "Tile") -> bool:
    return any(edge is not None and edge.is_river for edge in tile.edges.values())


def _has_feature(tile: "Tile", feature: HexFeature) -> bool:
    return any(current is feature for current in tile.features if current is not None)


def _geoform_id(value: object) -> int | None:
    if isinstance(value, int):
        return value

    raw_id = getattr(value, "id", None)
    return raw_id if isinstance(raw_id, int) else None


def _matches_geoform(tile: "Tile", *geoforms: GeoformType) -> bool:
    tile_geoform = tile.geoforms
    for geoform in geoforms:
        if tile_geoform == geoform:
            return True
        geoform_id = _geoform_id(geoform)
        if geoform_id is None:
            continue
        if _geoform_id(tile_geoform) == geoform_id:
            return True
    return False

def _weighted_tile_yield_score(
    tile: "Tile",
    profile: TileScoringProfile,
    tile_yield_score_cache: Dict[Tuple[int, int], float] | None = None,
) -> float:
    cache_key = (id(tile), id(profile))

    if tile_yield_score_cache is not None and cache_key in tile_yield_score_cache:
        return tile_yield_score_cache[cache_key]

    tile.calculate()
    yields = tile.get_tile_yield()

    score = (
        float(yields.food.value) * profile.food_weight
        + float(yields.production.value) * profile.production_weight
        + float(yields.gold.value) * profile.gold_weight
        + float(yields.science.value) * profile.science_weight
        + float(yields.culture.value) * profile.culture_weight
        + float(yields.housing.value) * profile.housing_weight
    )

    if tile_yield_score_cache is not None:
        tile_yield_score_cache[cache_key] = score

    return score

def _get_cached_neighbors(
    tile: "Tile",
    radius: int,
    neighbor_cache: Dict[Tuple[int, int], List["Tile"]] | None = None,
) -> List["Tile"]:
    if neighbor_cache is None:
        return TileRepository.get_neighbors(tile, radius=radius)

    cache_key = (id(tile), radius)
    if cache_key not in neighbor_cache:
        neighbor_cache[cache_key] = TileRepository.get_neighbors(tile, radius=radius)

    return neighbor_cache[cache_key]
