from collections.abc import Callable, Sequence
from typing import Any

from helpers.tiles import Tiles
from system.subsystems.hexgen.enums import GeoformType, HexFeature


type NeighborOffset = tuple[int, int]
type NeighborOffsetsProvider = Callable[[int], list[NeighborOffset]]
type RenderPositionResolver = Callable[[int, int], tuple[float, float]]
type RawHexGrid = Sequence[Sequence[Any]]


class WorldParams:
    (
        arctic,
        tundra,
        alpine_tundra,
        desert,
        scrubland,
        savanna,
        grasslands,
        boreal_forest,
        temperate_forest,
        temperate_rainforest,
        tropical_forest,
        tropical_rainforest,
        wasteland,
    ) = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13)

    desert_temperature_threshold = 17
    grass_temperature_upper_threshold = 30
    grass_temperature_lower_threshold = 10
    forest_lower_threshold = 5.0
    moisture_threshold_mangrove_jungle = 16
    moisture_threshold_heavy_forest = 10
    moisture_threshold_tundra_snow_lower = 2
    moisture_threshold_grassland_lower = 4
    light_jungle_temperature_threshold = 30
    cold_forrest_temperature_threshold = 8
    scrubland_temperature_threshold = 4
    flat_to_hills_threshold = 170
    hills_to_mountains_threshold = 217


_BIOME_NAME_TO_ID: dict[str, int] = {
    "arctic": WorldParams.arctic,
    "tundra": WorldParams.tundra,
    "alpine_tundra": WorldParams.alpine_tundra,
    "desert": WorldParams.desert,
    "scrubland": WorldParams.scrubland,
    "shrubland": WorldParams.scrubland,
    "savanna": WorldParams.savanna,
    "savannah": WorldParams.savanna,
    "grasslands": WorldParams.grasslands,
    "boreal_forest": WorldParams.boreal_forest,
    "temperate_forest": WorldParams.temperate_forest,
    "temperate_rainforest": WorldParams.temperate_rainforest,
    "tropical_forest": WorldParams.tropical_forest,
    "tropical_rainforest": WorldParams.tropical_rainforest,
}

_DESERT_TERRAINS = frozenset({"FlatDesert", "HillsDesert"})
_TUNDRA_TERRAINS = frozenset({"FlatTundra"})


def biome_id_for_hex(hex_tile: Any, *, default_biome_id: int = WorldParams.grasslands) -> int:
    biome_id = getattr(hex_tile, "biome_id", getattr(getattr(hex_tile, "biome", None), "id", None))
    if isinstance(biome_id, int):
        return biome_id

    biome = getattr(hex_tile, "biome", None)
    biome_key = str(getattr(biome, "name", "grasslands")).strip().lower()
    return _BIOME_NAME_TO_ID.get(biome_key, default_biome_id)


def classify_hex_terrain(hex_tile: Any) -> str:
    biome_id = biome_id_for_hex(hex_tile)
    biome = getattr(hex_tile, "biome", None)
    biome_name = str(getattr(biome, "name", biome_id))

    raw_temperature = getattr(hex_tile, "temperature", getattr(hex_tile, "base_temperature", (0.0,)))
    if isinstance(raw_temperature, list | tuple) and raw_temperature:
        hex_temp = float(raw_temperature[0])
    else:
        hex_temp = float(raw_temperature)

    hex_temp_i = int(round(hex_temp))
    moisture_like = float(hex_tile.moisture)
    geotype = getattr(hex_tile, "geoform_type", None)
    hex_alt = int(hex_tile.altitude)
    features = getattr(hex_tile, "features", ())

    if HexFeature.volcano in features:
        return "Volcano"

    if bool(hex_tile.is_water):
        if geotype == GeoformType.lake:
            return "Lake"
        if bool(getattr(hex_tile, "is_coast", False)):
            return "Coast"
        if geotype in (GeoformType.sea, GeoformType.ocean) and hex_temp < -1:
            return "SeaIce"
        return "Sea"

    if float(hex_tile.altitude) > WorldParams.hills_to_mountains_threshold:
        return "MountainSnow" if hex_temp_i < -2 else "Mountain"

    if hex_alt > WorldParams.flat_to_hills_threshold:
        if biome_id not in (WorldParams.scrubland, WorldParams.savanna, WorldParams.desert) and hex_temp_i < 0:
            return "HillsSnow"
        if biome_id in (WorldParams.savanna, WorldParams.desert):
            return "HillsDesert"
        if (
            biome_id in (WorldParams.grasslands, WorldParams.scrubland)
            and WorldParams.forest_lower_threshold <= hex_temp <= WorldParams.grass_temperature_upper_threshold
            and moisture_like < WorldParams.forest_lower_threshold
        ):
            return "HillsGrassland"
        if (
            biome_id
            in (
                WorldParams.grasslands,
                WorldParams.tropical_forest,
                WorldParams.temperate_rainforest,
                WorldParams.temperate_forest,
                WorldParams.boreal_forest,
                WorldParams.scrubland,
            )
            and moisture_like >= WorldParams.forest_lower_threshold
        ):
            return "HillsForest"
        if hex_temp < WorldParams.forest_lower_threshold and biome_id not in (
            WorldParams.scrubland,
            WorldParams.savanna,
            WorldParams.desert,
        ):
            return "HillsTundra"

    if biome_id == WorldParams.tropical_forest:
        return "FlatLightJungle"
    if biome_id == WorldParams.temperate_rainforest:
        return "FlatJungle"
    if biome_id == WorldParams.grasslands:
        return "FlatGrass"
    if biome_id == WorldParams.desert:
        return "FlatDesert"
    if biome_id == WorldParams.temperate_forest:
        if moisture_like < WorldParams.moisture_threshold_heavy_forest:
            return "FlatForest"
        return "FlatHeavyForest"
    if biome_id == WorldParams.boreal_forest:
        return "FlatPineForest"
    if biome_id == WorldParams.tropical_rainforest:
        return "FlatForest"
    if biome_id == WorldParams.savanna:
        return "FlatSavanna"
    if biome_id == WorldParams.scrubland:
        return "FlatScrubland"
    if biome_id == WorldParams.arctic:
        return "FlatIce"
    if biome_id == WorldParams.alpine_tundra:
        return "FlatTundraSnow"
    if biome_id == WorldParams.tundra:
        return "FlatTundra"

    raise ValueError(f"Could not classify terrain for hex {hex_tile} with biome '{biome_name}' (id {biome_id})")


def classify_visible_hexes(
    raw_grid: RawHexGrid,
    *,
    width: int,
    height: int,
    render_position_resolver: RenderPositionResolver | None = None,
) -> None:
    for col in range(height):
        for row in range(width):
            hex_tile = raw_grid[col][row]
            hex_tile.terrain = classify_hex_terrain(hex_tile)
            if render_position_resolver is not None:
                hex_tile.render_pos = render_position_resolver(col, row)


def adjust_water_levels(
    raw_grid: RawHexGrid,
    *,
    width: int,
    height: int,
    neighbor_offsets_provider: NeighborOffsetsProvider = Tiles.get_directions_per_col,
) -> None:
    visited: set[tuple[int, int]] = set()

    def neighbors(col: int, row: int) -> list[tuple[int, int]]:
        result: list[tuple[int, int]] = []
        for delta_col, delta_row in neighbor_offsets_provider(col):
            next_col = col + delta_col
            next_row = row + delta_row
            if 0 <= next_col < height and 0 <= next_row < width:
                result.append((next_col, next_row))
        return result

    for col in range(height):
        for row in range(width):
            hex_tile = raw_grid[col][row]
            if not hex_tile.is_water or (col, row) in visited:
                continue

            queue = [(col, row)]
            visited.add((col, row))
            water_cluster = [(col, row)]
            index = 0
            while index < len(queue):
                current_col, current_row = queue[index]
                index += 1
                for next_col, next_row in neighbors(current_col, current_row):
                    neighbor_hex = raw_grid[next_col][next_row]
                    if neighbor_hex.is_water and (next_col, next_row) not in visited:
                        visited.add((next_col, next_row))
                        queue.append((next_col, next_row))
                        water_cluster.append((next_col, next_row))

            border_altitudes: list[float] = []
            for water_col, water_row in water_cluster:
                for next_col, next_row in neighbors(water_col, water_row):
                    neighbor_hex = raw_grid[next_col][next_row]
                    if neighbor_hex.is_land:
                        border_altitudes.append(float(neighbor_hex.altitude))

            if not border_altitudes:
                continue

            water_level = min(border_altitudes) - 1
            for water_col, water_row in water_cluster:
                raw_grid[water_col][water_row].altitude = water_level


def promote_single_sea_between_coasts(raw_grid: RawHexGrid, *, width: int, height: int) -> int:
    to_promote: list[tuple[int, int]] = []

    def side_value(side: Any) -> int:
        try:
            return int(side.value[0])
        except Exception:
            return int(side)

    for col in range(height):
        for row in range(width):
            hex_tile = raw_grid[col][row]
            if not hex_tile.is_water or getattr(hex_tile, "terrain", "") != "Sea":
                continue

            coast_dirs: list[int] = []
            for side, neighbor in hex_tile.neighbors:
                if neighbor.is_water and getattr(neighbor, "terrain", "") == "Coast":
                    coast_dirs.append(side_value(side))

            opposites = {(direction + 3) % 6 for direction in coast_dirs}
            if any(direction in opposites for direction in coast_dirs):
                to_promote.append((col, row))

    for col, row in to_promote:
        raw_grid[col][row].terrain = "Coast"

    return len(to_promote)


def desertize_adjacent_tundra(raw_grid: RawHexGrid, *, width: int, height: int) -> int:
    to_convert: list[tuple[int, int]] = []

    for col in range(height):
        for row in range(width):
            hex_tile = raw_grid[col][row]
            if getattr(hex_tile, "terrain", "") not in _TUNDRA_TERRAINS:
                continue

            for _, neighbor in hex_tile.neighbors:
                if getattr(neighbor, "terrain", "") in _DESERT_TERRAINS:
                    to_convert.append((col, row))
                    break

    for col, row in to_convert:
        raw_grid[col][row].terrain = "FlatDesert"

    return len(to_convert)
