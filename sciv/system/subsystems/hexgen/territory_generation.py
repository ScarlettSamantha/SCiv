import heapq
import random
from dataclasses import dataclass, field
from itertools import count
from typing import TYPE_CHECKING, Any, Protocol, cast

from system.subsystems.hexgen.territory import Territory

if TYPE_CHECKING:
    from system.subsystems.hexgen.hex import Hex
else:
    Hex = Any


def _new_hex_float_cache() -> dict[Hex, float]:
    return {}


_TERRITORY_NAME_PREFIXES: dict[str, tuple[str, ...]] = {
    "desert": ("Amber", "Sun", "Dune", "Saffron", "Dust"),
    "savanna": ("Golden", "Acacia", "Sun", "Redgrass", "Drywind"),
    "grasslands": ("Green", "Open", "Meadow", "Bright", "Wind"),
    "shrubland": ("Briar", "Stone", "Heather", "Brush", "Grey"),
    "tundra": ("Frost", "White", "North", "Glacier", "Ice"),
    "arctic": ("Aurora", "Winter", "Snow", "Polar", "Blue"),
    "temperate_forest": ("Oak", "Moss", "Fern", "Green", "Sylvan"),
    "temperate_rainforest": ("Mist", "Rain", "Deep", "Moss", "Silver"),
    "tropical_forest": ("Emerald", "Canopy", "Jade", "Verdant", "Wild"),
    "tropical_rainforest": ("Storm", "Deep", "Jungle", "Verdant", "Monsoon"),
    "boreal_forest": ("Pine", "Spruce", "Taiga", "Needle", "Cold"),
}

_TERRITORY_NAME_BASE_SUFFIXES: tuple[str, ...] = (
    "Reach",
    "March",
    "Hold",
    "Basin",
    "Crown",
    "Wilds",
    "Expanse",
    "Frontier",
    "Domain",
    "Range",
)

_TERRITORY_NAME_COASTAL_SUFFIXES: tuple[str, ...] = (
    "Coast",
    "Shore",
    "Bay",
    "Sound",
    "Cape",
    "Strand",
)

_TERRITORY_NAME_LANDLOCKED_SUFFIXES: tuple[str, ...] = (
    "Vale",
    "Steppe",
    "Heights",
    "Basin",
    "Rise",
    "March",
)

_TERRITORY_NAME_RIVER_SUFFIXES: tuple[str, ...] = (
    "Ford",
    "Wash",
    "Channel",
    "Run",
    "Flow",
    "Reach",
)


class TerritoryMapGen(Protocol):
    debug: bool
    params: dict[str, Any]
    rng: random.Random
    hex_grid: Any
    territories: list[Territory]

    def _local_ruggedness(self, h: Hex) -> float: ...

    def hex_distance(self, a: tuple[int, int], b: tuple[int, int]) -> int: ...


@dataclass(slots=True)
class TerritoryGenerationContext:
    mapgen: TerritoryMapGen
    ruggedness_cache: dict[Hex, float] = field(default_factory=_new_hex_float_cache)
    temperature_cache: dict[Hex, float] = field(default_factory=_new_hex_float_cache)


def _mapgen_local_ruggedness(context: TerritoryGenerationContext, hex_tile: Hex) -> float:
    return context.mapgen._local_ruggedness(hex_tile)  # pyright: ignore[reportPrivateUsage]


def _territory_temperature(context: TerritoryGenerationContext, hex_tile: Hex) -> float:
    cached_value = context.temperature_cache.get(hex_tile)
    if cached_value is not None:
        return float(cached_value)

    raw_temperature = getattr(hex_tile, "temperature", 0.0)
    if isinstance(raw_temperature, tuple) and raw_temperature:
        first_value = cast(object, raw_temperature[0])
        value = float(first_value) if isinstance(first_value, (int, float)) else 0.0
    elif isinstance(raw_temperature, list) and raw_temperature:
        first_value = cast(object, raw_temperature[0])
        value = float(first_value) if isinstance(first_value, (int, float)) else 0.0
    elif isinstance(raw_temperature, (int, float)):
        value = float(raw_temperature)
    else:
        value = 0.0

    context.temperature_cache[hex_tile] = value
    return value


def _territory_ruggedness(context: TerritoryGenerationContext, hex_tile: Hex) -> float:
    cached_value = context.ruggedness_cache.get(hex_tile)
    if cached_value is not None:
        return float(cached_value)

    ruggedness = _mapgen_local_ruggedness(context, hex_tile)
    context.ruggedness_cache[hex_tile] = ruggedness
    return ruggedness


def _territory_seed_score(context: TerritoryGenerationContext, hex_tile: Hex) -> float:
    if not hex_tile.is_land:
        return float("-inf")

    altitude_above_sea = max(0.0, float(hex_tile.altitude) - float(context.mapgen.hex_grid.sealevel))
    ruggedness = _territory_ruggedness(context, hex_tile)
    temperature = _territory_temperature(context, hex_tile)
    coast_distance = float(getattr(hex_tile, "distance", 0.0))
    land_neighbors = sum(1 for _, neighbor in hex_tile.neighbors if neighbor.is_land)

    river_bonus = 2.8 if any(edge is not None and edge.is_river for edge in hex_tile.edges) else 0.0
    if river_bonus == 0.0:
        for _, neighbor in hex_tile.neighbors:
            if any(edge is not None and edge.is_river for edge in neighbor.edges):
                river_bonus = 1.2
                break

    coast_preference = 2.1 - abs(min(coast_distance, 6.0) - 2.5) * 0.7
    openness_bonus = max(-2.0, (land_neighbors - 3.0) * 0.45)
    moisture_bonus = min(2.0, float(getattr(hex_tile, "moisture", 0.0)) * 0.18)

    climate_penalty = 0.0
    if temperature < -8.0:
        climate_penalty += min(3.0, abs(temperature + 8.0) * 0.16)
    elif temperature > 32.0:
        climate_penalty += min(2.0, (temperature - 32.0) * 0.12)

    altitude_penalty = altitude_above_sea / 24.0
    ruggedness_penalty = ruggedness / 6.5
    if altitude_above_sea > 72.0:
        altitude_penalty += 2.0
    if altitude_above_sea > 108.0:
        altitude_penalty += 3.0
    if ruggedness > 16.0:
        ruggedness_penalty += 1.5
    if ruggedness > 24.0:
        ruggedness_penalty += 2.5

    return (
        12.0
        + river_bonus
        + coast_preference
        + openness_bonus
        + moisture_bonus
        - climate_penalty
        - altitude_penalty
        - ruggedness_penalty
    )


def _find_land_components(
    context: TerritoryGenerationContext,
    *,
    only_unowned: bool = False,
) -> list[set[Hex]]:
    visited: set[Hex] = set()
    components: list[set[Hex]] = []

    for start_hex in context.mapgen.hex_grid.hexes:
        if not start_hex.is_land or start_hex in visited:
            continue
        if only_unowned and start_hex.territory is not None:
            continue

        component: set[Hex] = set()
        queue: list[Hex] = [start_hex]
        visited.add(start_hex)

        while queue:
            current = queue.pop()
            component.add(current)
            for _, neighbor in current.neighbors:
                if not neighbor.is_land or neighbor in visited:
                    continue
                if only_unowned and neighbor.territory is not None:
                    continue
                visited.add(neighbor)
                queue.append(neighbor)

        if component:
            components.append(component)

    components.sort(key=len, reverse=True)
    return components


def _territory_seed_targets(land_components: list[set[Hex]], target: int) -> list[int]:
    if not land_components or target <= 0:
        return [0 for _ in land_components]

    component_count = len(land_components)
    total_land = sum(len(component) for component in land_components)
    targets = [0 for _ in land_components]

    if target >= component_count:
        targets = [1 for _ in land_components]
        remaining = target - component_count

        if remaining > 0 and total_land > 0:
            fractional_shares: list[tuple[float, int, int]] = []
            assigned_additional = 0

            for index, component in enumerate(land_components):
                ideal = (len(component) / total_land) * remaining
                whole = int(ideal)
                targets[index] += whole
                assigned_additional += whole
                fractional_shares.append((ideal - whole, len(component), index))

            fractional_shares.sort(reverse=True)
            for _fraction, _size, index in fractional_shares[: max(0, remaining - assigned_additional)]:
                targets[index] += 1
    else:
        for index in range(target):
            targets[index] = 1

    orphan_threshold = max(10, total_land // max(1, target * 4))
    for index, component in enumerate(land_components):
        if targets[index] == 0 and len(component) >= orphan_threshold:
            targets[index] = 1
        targets[index] = min(targets[index], len(component))

    return targets


def _pick_component_seeds(
    context: TerritoryGenerationContext,
    component: set[Hex],
    seed_target: int,
) -> list[Hex]:
    if seed_target <= 0 or not component:
        return []

    candidates = sorted(component, key=lambda current: _territory_seed_score(context, current), reverse=True)
    chosen: list[Hex] = []
    chosen_set: set[Hex] = set()
    spacing = min(8, max(2, int(round(((len(component) / max(1, seed_target)) ** 0.5) * 0.45))))

    current_spacing = spacing
    while len(chosen) < seed_target and current_spacing >= 0:
        for candidate in candidates:
            if candidate in chosen_set:
                continue
            if current_spacing > 0 and any(
                context.mapgen.hex_distance((candidate.x, candidate.y), (other.x, other.y)) < current_spacing
                for other in chosen
            ):
                continue

            chosen.append(candidate)
            chosen_set.add(candidate)
            if len(chosen) >= seed_target:
                break

        current_spacing -= 1

    if len(chosen) < seed_target:
        for candidate in candidates:
            if candidate in chosen_set:
                continue
            chosen.append(candidate)
            chosen_set.add(candidate)
            if len(chosen) >= seed_target:
                break

    return chosen


def _territory_step_cost(context: TerritoryGenerationContext, current: Hex, neighbor: Hex) -> float:
    current_alt = float(current.altitude)
    neighbor_alt = float(neighbor.altitude)
    climb = max(0.0, neighbor_alt - current_alt)
    descent = max(0.0, current_alt - neighbor_alt)
    ruggedness = (_territory_ruggedness(context, current) + _territory_ruggedness(context, neighbor)) / 2.0
    elevation = max(0.0, neighbor_alt - float(context.mapgen.hex_grid.sealevel))
    temperature_delta = abs(_territory_temperature(context, current) - _territory_temperature(context, neighbor))
    moisture_delta = abs(float(current.moisture) - float(neighbor.moisture))
    coast_delta = abs(float(getattr(current, "distance", 0.0)) - float(getattr(neighbor, "distance", 0.0)))

    river_penalty = 0.0
    side = current.get_side_to(neighbor)
    edge = current.get_edge(side) if side is not None else None
    if edge is not None and edge.is_river:
        river_penalty = 4.25

    cost = 1.0
    cost += climb / 18.0
    cost += descent / 40.0
    cost += ruggedness / 10.0
    cost += elevation / 100.0
    cost += temperature_delta / 16.0
    cost += moisture_delta / 12.0
    cost += min(1.8, coast_delta * 0.18)
    cost += river_penalty

    if elevation > 72.0:
        cost += 1.4
    if elevation > 110.0:
        cost += 2.2
    if ruggedness > 18.0:
        cost += 1.1
    if ruggedness > 28.0:
        cost += 2.0
    if current.is_coast_land != neighbor.is_coast_land:
        cost += 0.4

    return max(0.35, cost)


def _claim_land_component(
    context: TerritoryGenerationContext,
    component: set[Hex],
    territories: list[Territory],
) -> None:
    if not component or not territories:
        return

    territory_lookup = {territory.id: territory for territory in territories}
    frontier: list[tuple[float, int, int, Hex]] = []
    best_costs: dict[Hex, float] = {}
    tie_breaker = count()

    for territory in territories:
        territory.main.territory = territory
        territory.members = [territory.main]
        territory.last_added = [territory.main]
        best_costs[territory.main] = 0.0

        for _, neighbor in territory.main.neighbors:
            if neighbor not in component or not neighbor.is_land or neighbor.territory is not None:
                continue

            step_cost = _territory_step_cost(context, territory.main, neighbor)
            if step_cost >= best_costs.get(neighbor, float("inf")):
                continue

            best_costs[neighbor] = step_cost
            heapq.heappush(frontier, (step_cost, next(tie_breaker), territory.id, neighbor))

    while frontier:
        cost, _order, territory_id, current = heapq.heappop(frontier)
        if current.territory is not None:
            continue
        if cost > best_costs.get(current, float("inf")):
            continue

        territory = territory_lookup[territory_id]
        current.territory = territory
        territory.members.append(current)
        territory.last_added = [current]

        for _, neighbor in current.neighbors:
            if neighbor not in component or not neighbor.is_land or neighbor.territory is not None:
                continue

            next_cost = cost + _territory_step_cost(context, current, neighbor)
            if next_cost >= best_costs.get(neighbor, float("inf")):
                continue

            best_costs[neighbor] = next_cost
            heapq.heappush(frontier, (next_cost, next(tie_breaker), territory_id, neighbor))


def _nearest_territory_for_component(context: TerritoryGenerationContext, anchor_hex: Hex) -> Territory | None:
    if not context.mapgen.territories:
        return None

    anchor_temperature = _territory_temperature(context, anchor_hex)
    return min(
        context.mapgen.territories,
        key=lambda territory: (
            context.mapgen.hex_distance((anchor_hex.x, anchor_hex.y), (territory.main.x, territory.main.y))
            + abs(anchor_temperature - _territory_temperature(context, territory.main)) / 14.0,
            territory.id,
        ),
    )


def _assign_orphan_component(
    context: TerritoryGenerationContext,
    component: set[Hex],
    next_id: int,
) -> int:
    if not component:
        return next_id

    anchor_hex = max(component, key=lambda current: _territory_seed_score(context, current))
    average_size = max(
        1,
        sum(territory.size for territory in context.mapgen.territories) // max(1, len(context.mapgen.territories)),
    )
    should_create_territory = not context.mapgen.territories or len(component) >= max(16, average_size // 2)

    if should_create_territory:
        color = (
            context.mapgen.rng.randint(0, 255),
            context.mapgen.rng.randint(0, 255),
            context.mapgen.rng.randint(0, 255),
        )
        territory = Territory(context.mapgen.hex_grid, anchor_hex, next_id, color)
        territory.members = [anchor_hex]
        territory.last_added = [anchor_hex]
        context.mapgen.territories.append(territory)
        next_id += 1
    else:
        territory = _nearest_territory_for_component(context, anchor_hex)
        if territory is None:
            return next_id

    for hex_tile in component:
        if hex_tile is anchor_hex and hex_tile.territory is territory:
            continue
        hex_tile.territory = territory
        territory.members.append(hex_tile)

    territory.last_added = territory.members[-min(4, len(territory.members)) :]
    return next_id


def _refresh_territory_members(context: TerritoryGenerationContext) -> None:
    members_by_id: dict[int, list[Hex]] = {territory.id: [] for territory in context.mapgen.territories}

    for hex_tile in context.mapgen.hex_grid.hexes:
        territory = hex_tile.territory
        if territory is None:
            continue
        if not hex_tile.is_land:
            hex_tile.territory = None
            continue
        members_by_id.setdefault(territory.id, []).append(hex_tile)

    active_territories: list[Territory] = []
    for territory in context.mapgen.territories:
        members = members_by_id.get(territory.id, [])
        if not members:
            territory.members = []
            territory.last_added = []
            continue

        territory.members = members
        territory.last_added = members[-min(4, len(members)) :]
        active_territories.append(territory)

    context.mapgen.territories = active_territories


def _merge_barren_territories(context: TerritoryGenerationContext) -> None:
    if not context.mapgen.territories:
        return

    average_size = max(
        1,
        sum(territory.size for territory in context.mapgen.territories) // len(context.mapgen.territories),
    )
    barren_size_limit = max(8, average_size // 2)
    changed = True

    while changed:
        changed = False
        for territory in sorted(context.mapgen.territories, key=lambda current: current.size):
            if territory.size == 0 or territory.avg_temp() >= 0 or territory.size >= barren_size_limit:
                continue

            neighbors = [neighbor for neighbor in territory.neighbors if neighbor.size > 0]
            if not neighbors:
                continue

            merge_target = min(
                neighbors,
                key=lambda neighbor: (
                    abs(neighbor.avg_temp() - territory.avg_temp()),
                    context.mapgen.hex_distance((territory.main.x, territory.main.y), (neighbor.main.x, neighbor.main.y)),
                    neighbor.id,
                ),
            )

            for member in territory.members:
                member.territory = merge_target
            territory.members = []
            territory.last_added = []
            changed = True

        if changed:
            _refresh_territory_members(context)


def _territory_dominant_biome_key(territory: Territory) -> str:
    if not territory.biomes:
        return "unknown"

    biome = territory.biomes[0].get("biome")
    biome_name = getattr(biome, "name", None)
    return str(biome_name) if isinstance(biome_name, str) and biome_name else "unknown"


def _territory_name_prefix_options(territory: Territory) -> tuple[str, ...]:
    biome_key = _territory_dominant_biome_key(territory)
    biome_prefixes = _TERRITORY_NAME_PREFIXES.get(biome_key)
    if biome_prefixes is not None:
        return biome_prefixes

    if territory.landlocked:
        return ("High", "Grey", "Inner", "Old", "Stone")
    return ("Green", "Silver", "High", "Grand", "North")


def _territory_name_suffix_options(territory: Territory) -> tuple[str, ...]:
    has_river = any(any(edge is not None and edge.is_river for edge in member.edges) for member in territory.members)
    if has_river:
        return _TERRITORY_NAME_RIVER_SUFFIXES
    if territory.landlocked:
        return _TERRITORY_NAME_LANDLOCKED_SUFFIXES
    return _TERRITORY_NAME_COASTAL_SUFFIXES + _TERRITORY_NAME_BASE_SUFFIXES


def _territory_name_candidates(context: TerritoryGenerationContext, territory: Territory) -> list[str]:
    prefixes = list(_territory_name_prefix_options(territory))
    suffixes = list(_territory_name_suffix_options(territory))
    context.mapgen.rng.shuffle(prefixes)
    context.mapgen.rng.shuffle(suffixes)

    candidates: list[str] = []
    for prefix in prefixes:
        for suffix in suffixes:
            candidates.append(f"{prefix} {suffix}")

    return candidates


def _assign_territory_names(context: TerritoryGenerationContext) -> None:
    used_names: set[str] = set()

    for territory in sorted(context.mapgen.territories, key=lambda current: (current.size, current.id), reverse=True):
        assigned_name: str | None = None
        for candidate in _territory_name_candidates(context, territory):
            if candidate in used_names:
                continue
            assigned_name = candidate
            break

        if assigned_name is None:
            assigned_name = f"Territory {territory.id}"

        territory.name = assigned_name
        used_names.add(assigned_name)


def generate_territories(mapgen: TerritoryMapGen) -> None:
    num_territories = int(mapgen.params.get("num_territories", 0))

    if mapgen.debug:
        print("Making {} territories".format(num_territories))

    if num_territories == 0:
        return

    context = TerritoryGenerationContext(mapgen=mapgen)
    land_components = _find_land_components(context)
    if not land_components:
        return

    target_territories = min(num_territories, sum(len(component) for component in land_components))
    seed_targets = _territory_seed_targets(land_components, target_territories)

    next_id = 0
    for component, seed_target in zip(land_components, seed_targets, strict=False):
        if seed_target <= 0:
            continue

        seeds = _pick_component_seeds(context, component, seed_target)
        if not seeds:
            continue

        component_territories: list[Territory] = []
        for seed_hex in seeds:
            color = (
                mapgen.rng.randint(0, 255),
                mapgen.rng.randint(0, 255),
                mapgen.rng.randint(0, 255),
            )
            territory = Territory(mapgen.hex_grid, seed_hex, next_id, color)
            mapgen.territories.append(territory)
            component_territories.append(territory)
            next_id += 1

        _claim_land_component(context, component, component_territories)

    orphan_components = _find_land_components(context, only_unowned=True)
    if orphan_components and mapgen.debug:
        print("Assigning {} orphan land components".format(len(orphan_components)))
    for component in orphan_components:
        next_id = _assign_orphan_component(context, component, next_id)

    _refresh_territory_members(context)

    if mapgen.debug:
        print("Merging barren territories")
    _merge_barren_territories(context)
    _refresh_territory_members(context)
    _assign_territory_names(context)

    if mapgen.debug:
        print("There are now {} territories".format(len(mapgen.territories)))
        print("Splitting territories into contiguous blocks")

    for hex_tile in mapgen.hex_grid.hexes:
        hex_tile.marked = False
    for territory in mapgen.territories:
        territory.find_groups()


__all__ = ["generate_territories"]
