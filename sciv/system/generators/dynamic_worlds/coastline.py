from typing import TYPE_CHECKING

from system.subsystems.hexgen.enums import GeoformType, HexFeature

if TYPE_CHECKING:
    from system.subsystems.hexgen.grid import Grid
    from system.subsystems.hexgen.hex import Hex


def apply_scripted_coastline_polish(hex_grid: "Grid", map_script: str) -> int:
    if map_script not in {"archipelago", "small_continents", "fractal"}:
        return 0

    to_promote: list[tuple[int, int]] = []

    for x, column in enumerate(hex_grid.grid):
        for y, _ in enumerate(column):
            hex_tile: "Hex" = hex_grid.grid[x][y]

            if not hex_tile.is_water or getattr(hex_tile, "terrain", "") != "Sea":
                continue

            neighbors = [neighbor for _, neighbor in hex_tile.neighbors]
            land_neighbors = [neighbor for neighbor in neighbors if neighbor.is_land]
            coast_neighbors = [neighbor for neighbor in neighbors if getattr(neighbor, "terrain", "") == "Coast"]
            island_neighbors = [
                neighbor
                for neighbor in land_neighbors
                if getattr(neighbor, "geoform_type", None) in {
                    GeoformType.small_island,
                    GeoformType.large_island,
                    GeoformType.peninsula,
                }
            ]

            narrow_water = any(feature in hex_tile.features for feature in {HexFeature.bay, HexFeature.strait})
            peninsula_touch = any(HexFeature.peninsula in neighbor.features for neighbor in land_neighbors)

            if map_script == "archipelago":
                should_promote = len(island_neighbors) >= 1 and (
                    len(land_neighbors) >= 2 or len(coast_neighbors) >= 2 or narrow_water or peninsula_touch
                )
            elif map_script == "small_continents":
                should_promote = len(island_neighbors) >= 1 and (
                    len(land_neighbors) >= 3 or len(coast_neighbors) >= 2 or peninsula_touch
                )
            else:
                should_promote = len(land_neighbors) >= 2 and (narrow_water or peninsula_touch)

            if should_promote:
                to_promote.append((x, y))

    for x, y in to_promote:
        hex_grid.grid[x][y].terrain = "Coast"

    return len(to_promote)
