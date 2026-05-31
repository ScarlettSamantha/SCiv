from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

from gameplay.founding.site_scoring import TileScoringProfile, rank_tiles, resolve_tile_scoring_profile
from gameplay.repositories.tile import TileRepository
from helpers.cache import Cache

if TYPE_CHECKING:
    from gameplay.player import Player
    from gameplay.tile import Tile
    from gameplay.unit import Unit


CITY_FOUNDING_DISTANCE_RADIUS_DEFAULT: int = 2
CITY_FOUNDING_IN_OWN_TERRITORY_DEFAULT: bool = True


@dataclass(frozen=True, slots=True)
class TileRecommendation:
    tile: "Tile"
    score: float


def recommend_founding_tiles(
    origin: "Tile",
    player: "Player",
    ignore_occupying_unit: "Unit | None" = None,
    search_radius: int = 8,
    limit: int = 5,
    profile: TileScoringProfile | None = None,
) -> list[TileRecommendation]:
    candidates = [
        tile
        for tile in [origin, *TileRepository.get_neighbors(origin, radius=search_radius)]
        if can_found_city_on_tile(tile, player, ignore_occupying_unit=ignore_occupying_unit)
    ]

    ranked = rank_tiles(
        candidates,
        profile=profile or resolve_tile_scoring_profile(),
        map_dimensions=_get_map_dimensions(),
        limit=limit,
    )
    return [TileRecommendation(tile=tile, score=score) for tile, score in ranked]


def find_best_founding_tile(
    origin: "Tile",
    player: "Player",
    ignore_occupying_unit: "Unit | None" = None,
    search_radius: int = 8,
    profile: TileScoringProfile | None = None,
) -> "Tile | None":
    recommendations = recommend_founding_tiles(
        origin,
        player,
        ignore_occupying_unit=ignore_occupying_unit,
        search_radius=search_radius,
        limit=1,
        profile=profile,
    )
    return recommendations[0].tile if recommendations else None


def format_founding_recommendations(recommendations: Sequence[TileRecommendation]) -> str:
    if not recommendations:
        return "No viable city sites nearby."

    parts = [
        f"({recommendation.tile.x}, {recommendation.tile.y}) {recommendation.score:.1f}"
        for recommendation in recommendations
    ]
    return "Best nearby sites: " + " | ".join(parts)


def can_found_city_on_tile(
    tile: "Tile",
    player: "Player",
    ignore_occupying_unit: "Unit | None" = None,
    city_distance_rule: int | None = None,
    city_founding_in_own_territory_rule: bool | None = None,
) -> bool:
    distance_rule, territory_rule = _resolve_founding_rules(city_distance_rule, city_founding_in_own_territory_rule)

    if tile.is_city():
        return False

    if tile.player is None:
        territory_ok = True
    elif tile.player != player:
        territory_ok = False
    else:
        territory_ok = territory_rule

    if not territory_ok:
        return False

    if not tile.is_passable():
        return False

    if len(TileRepository.get_cities_in_radius(tile, distance_rule)) > 0:
        return False

    units = [unit for unit in tile.units.all() if unit is not ignore_occupying_unit]
    if units:
        return False

    return True


def _resolve_founding_rules(
    city_distance_rule: int | None,
    city_founding_in_own_territory_rule: bool | None,
) -> tuple[int, bool]:
    if city_distance_rule is not None and city_founding_in_own_territory_rule is not None:
        return city_distance_rule, city_founding_in_own_territory_rule

    try:
        rules = Cache.get_active_rules()
    except AssertionError:
        return (
            city_distance_rule or CITY_FOUNDING_DISTANCE_RADIUS_DEFAULT,
            CITY_FOUNDING_IN_OWN_TERRITORY_DEFAULT
            if city_founding_in_own_territory_rule is None
            else city_founding_in_own_territory_rule,
        )

    return (
        city_distance_rule or int(rules.get_city_founding_distance_rule()),
        city_founding_in_own_territory_rule
        if city_founding_in_own_territory_rule is not None
        else bool(rules.get_city_founding_in_own_territory_rule()),
    )


def _get_map_dimensions() -> tuple[int, int]:
    try:
        settings = Cache.get_game_settings()
    except AssertionError:
        return (0, 0)
    return (int(settings.width), int(settings.height))