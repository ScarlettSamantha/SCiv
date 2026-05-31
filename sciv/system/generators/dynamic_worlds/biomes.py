from collections import deque
from collections.abc import Mapping, Set
from typing import TYPE_CHECKING
from uuid import uuid4

from system.generators.dynamic_worlds.models import HexCoord, NamedBiomeRegion
from system.generators.dynamic_worlds.names import build_seeded_rng, generate_biome_region_name
from system.subsystems.hexgen.enums import HexEdge

if TYPE_CHECKING:
    from gameplay.tile import Tile
    from system.subsystems.hexgen.grid import Grid
    from system.subsystems.hexgen.hex import Hex


def apply_biome_style_profile(
    hex_grid: "Grid",
    *,
    biome_style: str,
    seed: int | None,
) -> dict[str, float]:
    rng = build_seeded_rng(seed, f"biome-style:{biome_style}")
    equatorial_bonus = float(hex_grid.params.get("equatorial_moisture_bonus", 0.9))
    subtropical_dryness = float(hex_grid.params.get("subtropical_dryness_bonus", 0.8))
    polar_bonus = float(hex_grid.params.get("polar_moisture_bonus", 0.2))
    rain_shadow_multiplier = float(hex_grid.params.get("rain_shadow_multiplier", 1.0))
    coastal_bonus = float(hex_grid.params.get("coastal_moisture_bonus", 0.35))
    river_bonus = float(hex_grid.params.get("river_moisture_bonus", 0.3))
    rain_shadow_strength = float(hex_grid.params.get("rain_shadow_strength", 1.6))
    wind_dir = str(hex_grid.params.get("wind_dir", "west"))
    processed = 0
    total_delta = 0.0

    for hex_tile in hex_grid.hexes:
        if not hex_tile.is_land:
            continue

        latitude = float(hex_tile.latitude_ratio)
        coastal = any(neighbor.is_water for _, neighbor in hex_tile.neighbors)
        river_touched = any(edge is not None and getattr(edge, "is_river", False) for edge in hex_tile.edges)
        inland_distance = min(8.0, float(getattr(hex_tile, "distance", 0.0)))
        subtropical_band = max(0.0, 1.0 - abs(latitude - 0.58) / 0.24)
        polar_band = max(0.0, 1.0 - latitude)
        rain_shadow = _estimate_rain_shadow(hex_tile, wind_dir)

        delta = (
            equatorial_bonus * latitude
            - subtropical_dryness * subtropical_band
            + polar_bonus * polar_band
            - rain_shadow_multiplier * rain_shadow_strength * 0.18 * rain_shadow
        )

        if coastal:
            delta += coastal_bonus * (0.55 + 0.45 * latitude)
        if river_touched:
            delta += river_bonus
        if float(hex_tile.altitude) >= 170:
            delta -= 0.25
        if float(hex_tile.altitude) >= 217:
            delta -= 0.35

        if biome_style == "verdant":
            delta += 1.2 + 1.6 * latitude + 0.12 * inland_distance
            if coastal:
                delta += 0.8
            if river_touched:
                delta += 0.6
            delta += rng.uniform(-0.35, 0.35)
        elif biome_style == "arid":
            delta -= 1.0 + 2.9 * subtropical_band + 0.18 * inland_distance
            if coastal:
                delta += 0.95
            if river_touched:
                delta += 1.15
            delta += rng.uniform(-0.25, 0.25)
        elif biome_style == "frigid":
            delta += 0.5 + 1.35 * polar_band
            if coastal:
                delta += 0.35
            if river_touched:
                delta += 0.25
            delta += rng.uniform(-0.2, 0.2)

        hex_tile.moisture = max(0.0, float(hex_tile.moisture) + delta)
        processed += 1
        total_delta += delta

    return {
        "land_hexes_processed": float(processed),
        "avg_moisture_delta": round(total_delta / max(1, processed), 3),
    }


def _estimate_rain_shadow(hex_tile: "Hex", wind_dir: str) -> float:
    direction_sets: dict[str, tuple[HexEdge, ...]] = {
        "west": (HexEdge.west, HexEdge.north_west, HexEdge.south_west),
        "east": (HexEdge.east, HexEdge.north_east, HexEdge.south_east),
        "north": (HexEdge.north_west, HexEdge.north_east, HexEdge.west),
        "south": (HexEdge.south_west, HexEdge.south_east, HexEdge.east),
    }
    directions = direction_sets.get(wind_dir, direction_sets["west"])
    frontier = [hex_tile]
    visited = {hex_tile}
    pressure = 0.0

    for distance in range(1, 4):
        next_frontier: list[Hex] = []
        for current in frontier:
            for direction in directions:
                neighbor = current.neighbor_at(direction)
                if neighbor in visited or not neighbor.is_land:
                    continue
                visited.add(neighbor)
                next_frontier.append(neighbor)

                altitude = float(neighbor.altitude)
                if altitude >= 217:
                    pressure += 1.0 / distance
                elif altitude >= 170:
                    pressure += 0.55 / distance

        frontier = next_frontier

    return pressure


def build_named_biome_regions(
    hex_grid: "Grid",
    *,
    seed: int | None,
    visible_coords: Set[HexCoord] | None = None,
) -> list[NamedBiomeRegion]:
    rng = build_seeded_rng(seed, "biome-regions")
    used_names: set[str] = set()
    visited: set[HexCoord] = set()
    named_regions: list[NamedBiomeRegion] = []

    coords = sorted(visible_coords) if visible_coords is not None else sorted((hex_tile.x, hex_tile.y) for hex_tile in hex_grid.hexes)
    coord_set = set(coords) if visible_coords is None else set(visible_coords)

    for coord in coords:
        if coord in visited:
            continue

        start_hex = hex_grid.get(*coord)
        if start_hex is None or not start_hex.is_land:
            continue

        target_biome = start_hex.biome
        queue: deque[Hex] = deque([start_hex])
        region_coords: list[HexCoord] = []

        while queue:
            current = queue.popleft()
            current_coord = (current.x, current.y)

            if current_coord in visited or current_coord not in coord_set or not current.is_land:
                continue

            if current.biome.name != target_biome.name:
                continue

            visited.add(current_coord)
            region_coords.append(current_coord)

            for _, neighbor in current.neighbors:
                neighbor_coord = (neighbor.x, neighbor.y)
                if neighbor_coord not in visited:
                    queue.append(neighbor)

        if not region_coords:
            continue

        region_coords.sort()
        region_name = generate_biome_region_name(rng, target_biome.name, str(target_biome.title), used_names)
        named_regions.append(
            NamedBiomeRegion(
                id=uuid4().hex,
                name=region_name,
                biome_key=target_biome.name,
                biome_title=str(target_biome.title),
                size=len(region_coords),
                tiles=tuple(region_coords),
            )
        )

    named_regions.sort(key=lambda current: current.size, reverse=True)
    return named_regions


def apply_biome_region_names(tiles: Mapping[HexCoord, "Tile"], regions: list[NamedBiomeRegion]) -> None:
    for region in regions:
        for coord in region.tiles:
            tile = tiles.get(coord)
            if tile is None:
                continue

            setattr(tile, "biome_region_id", region.id)
            setattr(tile, "biome_region_name", region.name)
            setattr(tile, "biome_region_key", region.biome_key)
            setattr(tile, "biome_region_type", region.biome_title)
            setattr(tile, "biome_region_size", region.size)
