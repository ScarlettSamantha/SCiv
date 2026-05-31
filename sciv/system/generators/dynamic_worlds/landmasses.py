import math
import random
from collections.abc import Iterable, Mapping, Set
from typing import TYPE_CHECKING, cast

import numpy as np

from system.generators.dynamic_worlds.models import HexCoord, NamedLandmass
from system.generators.dynamic_worlds.names import build_seeded_rng, generate_landmass_name
from system.subsystems.hexgen.enums import GeoformType

if TYPE_CHECKING:
    from gameplay.tile import Tile
    from system.subsystems.hexgen.geoform import Geoform
    from system.subsystems.hexgen.heightmap import Heightmap

LAND_GEOFORM_TYPES = {
    GeoformType.continent,
    GeoformType.large_island,
    GeoformType.small_island,
    GeoformType.peninsula,
    GeoformType.isthmus,
}


def apply_landmass_heightmap_profile(heightmap: "Heightmap", *, map_script: str, rng: random.Random) -> dict[str, int]:
    x_axis, y_axis = _normalized_axes(heightmap.grid.shape[0])
    mask = _build_landmass_mask(map_script, x_axis, y_axis, rng)

    low, high = heightmap.params.get("height_range", (0, 255))
    heightmap.grid[:] = np.clip(heightmap.grid.astype(np.float64) + mask, float(low), float(high))

    channels = _carve_channels(heightmap, map_script=map_script, rng=rng)
    inland_seas = _carve_inland_seas(heightmap, rng=rng)

    _smooth_heightmap(
        heightmap.grid,
        passes=int(heightmap.params.get("height_smoothing_passes", 0)),
        strength=float(heightmap.params.get("height_smoothing_strength", 0.0)),
    )
    _compress_mountain_peaks(
        heightmap.grid,
        low=float(low),
        high=float(high),
        knee_ratio=float(heightmap.params.get("mountain_knee_ratio", 0.84)),
        compression_ratio=float(heightmap.params.get("mountain_compression_ratio", 1.0)),
    )

    heightmap.grid[:] = np.clip(heightmap.grid, float(low), float(high))
    _refresh_heightmap_stats(heightmap)
    return {"channels": channels, "inland_seas": inland_seas}


def _build_landmass_mask(
    map_script: str,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    rng: random.Random,
) -> np.ndarray:
    radial = np.sqrt(x_axis**2 + y_axis**2)

    if map_script == "pangaea":
        mask = 92.0 * np.clip(1.08 - radial * 1.12, 0.0, None)
        mask -= 22.0 * radial
        mask += _blob_field(
            x_axis,
            y_axis,
            [
                (0.0, 0.0, 50.0, 0.42),
                (rng.uniform(-0.18, 0.12), rng.uniform(-0.12, 0.12), 30.0, 0.26),
                (rng.uniform(-0.12, 0.18), rng.uniform(-0.12, 0.12), 24.0, 0.22),
            ],
        )
        mask += _wave_field(x_axis, y_axis, amplitude=12.0, x_frequency=1.8, y_frequency=2.2, rng=rng)
        return mask

    if map_script == "archipelago":
        mask = -58.0 - 10.0 * radial
        mask += _blob_field(
            x_axis,
            y_axis,
            _random_blob_specs(rng, count=18, spread=0.92, amplitude=(44.0, 88.0), sigma=(0.06, 0.15)),
        )
        mask += _wave_field(x_axis, y_axis, amplitude=26.0, x_frequency=4.0, y_frequency=4.6, rng=rng)
        return mask

    if map_script == "small_continents":
        mask = -26.0 - 6.0 * radial
        mask += _blob_field(
            x_axis,
            y_axis,
            _random_blob_specs(rng, count=8, spread=0.82, amplitude=(46.0, 76.0), sigma=(0.12, 0.24)),
        )
        mask += _wave_field(x_axis, y_axis, amplitude=18.0, x_frequency=3.0, y_frequency=3.6, rng=rng)
        return mask

    if map_script == "fractal":
        mask = -18.0 - 8.0 * radial
        mask += _blob_field(
            x_axis,
            y_axis,
            _random_blob_specs(rng, count=10, spread=0.88, amplitude=(38.0, 72.0), sigma=(0.10, 0.22)),
        )
        mask += _wave_field(x_axis, y_axis, amplitude=30.0, x_frequency=3.8, y_frequency=2.9, rng=rng)
        mask += 10.0 * np.sin((x_axis + y_axis) * math.pi * 2.6 + rng.random() * math.tau)
        return mask

    mask = -8.0 - 12.0 * radial
    mask += _blob_field(
        x_axis,
        y_axis,
        _random_blob_specs(rng, count=4, spread=0.72, amplitude=(50.0, 84.0), sigma=(0.16, 0.30)),
    )
    mask += _wave_field(x_axis, y_axis, amplitude=14.0, x_frequency=2.2, y_frequency=2.8, rng=rng)
    return mask


def _normalized_axes(size: int) -> tuple[np.ndarray, np.ndarray]:
    axis = np.linspace(-1.0, 1.0, size, dtype=np.float64)
    return np.meshgrid(axis, axis, indexing="ij")


def _random_blob_specs(
    rng: random.Random,
    *,
    count: int,
    spread: float,
    amplitude: tuple[float, float],
    sigma: tuple[float, float],
) -> list[tuple[float, float, float, float]]:
    return [
        (
            rng.uniform(-spread, spread),
            rng.uniform(-spread, spread),
            rng.uniform(*amplitude),
            rng.uniform(*sigma),
        )
        for _ in range(count)
    ]


def _blob_field(
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    blobs: list[tuple[float, float, float, float]],
) -> np.ndarray:
    field = np.zeros_like(x_axis, dtype=np.float64)
    for center_x, center_y, amplitude, sigma in blobs:
        exponent = ((x_axis - center_x) ** 2 + (y_axis - center_y) ** 2) / max(0.0001, 2.0 * sigma * sigma)
        field += amplitude * np.exp(-exponent)
    return field


def _wave_field(
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    *,
    amplitude: float,
    x_frequency: float,
    y_frequency: float,
    rng: random.Random,
) -> np.ndarray:
    phase_x = rng.random() * math.tau
    phase_y = rng.random() * math.tau
    return amplitude * (
        np.sin(x_axis * math.pi * x_frequency + phase_x)
        + 0.65 * np.cos(y_axis * math.pi * y_frequency + phase_y)
    )


def _smooth_heightmap(grid: np.ndarray, *, passes: int, strength: float) -> None:
    if passes <= 0 or strength <= 0.0:
        return

    blend = max(0.0, min(1.0, strength))
    for _ in range(passes):
        padded = np.pad(grid, 1, mode="edge")
        blurred = (
            4.0 * padded[1:-1, 1:-1]
            + 2.0 * (padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:])
            + padded[:-2, :-2]
            + padded[:-2, 2:]
            + padded[2:, :-2]
            + padded[2:, 2:]
        ) / 16.0
        grid[:] = grid * (1.0 - blend) + blurred * blend


def _compress_mountain_peaks(
    grid: np.ndarray,
    *,
    low: float,
    high: float,
    knee_ratio: float,
    compression_ratio: float,
) -> None:
    if compression_ratio >= 1.0:
        return

    clamped_knee_ratio = max(0.0, min(0.98, knee_ratio))
    clamped_compression_ratio = max(0.0, min(1.0, compression_ratio))
    knee = low + (high - low) * clamped_knee_ratio
    above = grid > knee
    if not np.any(above):
        return

    grid[above] = knee + (grid[above] - knee) * clamped_compression_ratio


def _refresh_heightmap_stats(heightmap: "Heightmap") -> None:
    heightmap.highest_height = int(np.max(heightmap.grid))
    heightmap.lowest_height = int(np.min(heightmap.grid))
    heightmap.average_height = int(np.mean(heightmap.grid))

    sea_percent = int(heightmap.params.get("sea_percent", 40))
    heightmap.sealevel = round(heightmap.average_height * (sea_percent * 2 / 100))
    if sea_percent == 100:
        heightmap.sealevel = 255


def _carve_channels(heightmap: "Heightmap", *, map_script: str, rng: random.Random) -> int:
    count = int(heightmap.params.get("channel_count", 0))
    if count <= 0:
        return 0

    grid = heightmap.grid
    size = grid.shape[0]
    axis_x, axis_y = _grid_axes(grid)
    base_depth = float(heightmap.params.get("channel_depth", 0.0))
    base_width = max(1.5, size * float(heightmap.params.get("channel_width_ratio", 0.035)))

    for channel_index in range(count):
        start, control, end = _channel_curve_points(size=size, map_script=map_script, rng=rng, channel_index=channel_index)
        _apply_curve_cut(
            grid,
            axis_x,
            axis_y,
            start=start,
            control=control,
            end=end,
            depth=base_depth * rng.uniform(0.9, 1.15),
            width=base_width * rng.uniform(0.85, 1.2),
        )

    return count


def _carve_inland_seas(heightmap: "Heightmap", *, rng: random.Random) -> int:
    count = int(heightmap.params.get("inland_sea_count", 0))
    if count <= 0:
        return 0

    grid = heightmap.grid
    size = grid.shape[0]
    axis_x, axis_y = _grid_axes(grid)
    base_depth = float(heightmap.params.get("inland_sea_depth", 0.0))
    base_radius = max(2.5, size * float(heightmap.params.get("inland_sea_radius_ratio", 0.08)))

    for _ in range(count):
        center_x = rng.uniform(size * 0.24, size * 0.76)
        center_y = rng.uniform(size * 0.24, size * 0.76)
        radius_x = base_radius * rng.uniform(0.8, 1.25)
        radius_y = base_radius * rng.uniform(0.75, 1.35)
        depth = base_depth * rng.uniform(0.9, 1.15)

        _apply_basin_cut(
            grid,
            axis_x,
            axis_y,
            center_x=center_x,
            center_y=center_y,
            radius_x=radius_x,
            radius_y=radius_y,
            depth=depth,
        )

        for _ in range(rng.randint(1, 2)):
            _apply_basin_cut(
                grid,
                axis_x,
                axis_y,
                center_x=center_x + rng.uniform(-radius_x * 0.55, radius_x * 0.55),
                center_y=center_y + rng.uniform(-radius_y * 0.55, radius_y * 0.55),
                radius_x=radius_x * rng.uniform(0.35, 0.65),
                radius_y=radius_y * rng.uniform(0.35, 0.65),
                depth=depth * rng.uniform(0.35, 0.6),
            )

    return count


def _channel_curve_points(
    *,
    size: int,
    map_script: str,
    rng: random.Random,
    channel_index: int,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    orientations: dict[str, tuple[str, ...]] = {
        "pangaea": ("east_west",),
        "continents": ("east_west", "north_south"),
        "small_continents": ("east_west", "north_south", "diag_a"),
        "archipelago": ("diag_a", "diag_b", "east_west"),
        "fractal": ("east_west", "north_south", "diag_a", "diag_b"),
    }
    orientation_pool = orientations.get(map_script, ("east_west", "north_south"))
    orientation = orientation_pool[channel_index % len(orientation_pool)] if map_script == "pangaea" else rng.choice(orientation_pool)
    jitter = size * 0.18

    if orientation == "north_south":
        start = (0.0, rng.uniform(size * 0.25, size * 0.75))
        end = (size - 1.0, rng.uniform(size * 0.25, size * 0.75))
    elif orientation == "diag_a":
        start = (0.0, rng.uniform(size * 0.12, size * 0.34))
        end = (size - 1.0, rng.uniform(size * 0.66, size * 0.88))
    elif orientation == "diag_b":
        start = (0.0, rng.uniform(size * 0.66, size * 0.88))
        end = (size - 1.0, rng.uniform(size * 0.12, size * 0.34))
    else:
        start = (rng.uniform(size * 0.25, size * 0.75), 0.0)
        end = (rng.uniform(size * 0.25, size * 0.75), size - 1.0)

    control = (
        size * 0.5 + rng.uniform(-jitter, jitter),
        size * 0.5 + rng.uniform(-jitter, jitter),
    )
    return start, control, end


def _apply_curve_cut(
    grid: np.ndarray,
    axis_x: np.ndarray,
    axis_y: np.ndarray,
    *,
    start: tuple[float, float],
    control: tuple[float, float],
    end: tuple[float, float],
    depth: float,
    width: float,
) -> None:
    steps = max(18, int(grid.shape[0] * 0.45))
    point_depth = depth / max(1.0, width * 1.8)

    for t in np.linspace(0.0, 1.0, steps):
        omt = 1.0 - float(t)
        point_x = omt * omt * start[0] + 2.0 * omt * float(t) * control[0] + float(t) * float(t) * end[0]
        point_y = omt * omt * start[1] + 2.0 * omt * float(t) * control[1] + float(t) * float(t) * end[1]
        dist_sq = (axis_x - point_x) ** 2 + (axis_y - point_y) ** 2
        grid -= point_depth * np.exp(-dist_sq / max(1.0, 2.0 * width * width))


def _apply_basin_cut(
    grid: np.ndarray,
    axis_x: np.ndarray,
    axis_y: np.ndarray,
    *,
    center_x: float,
    center_y: float,
    radius_x: float,
    radius_y: float,
    depth: float,
) -> None:
    scaled = ((axis_x - center_x) / max(1.0, radius_x)) ** 2 + ((axis_y - center_y) / max(1.0, radius_y)) ** 2
    grid -= depth * np.exp(-scaled * 2.3)


def _grid_axes(grid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    axis_indices = np.indices(grid.shape, dtype=np.float64)
    axis_x = cast(np.ndarray, axis_indices[0])
    axis_y = cast(np.ndarray, axis_indices[1])
    return axis_x, axis_y


def _geoform_title(geoform_type: GeoformType) -> str:
    return str(geoform_type.value[1])


def build_named_landmasses(
    geoforms: Iterable["Geoform"],
    *,
    seed: int | None,
    visible_coords: Set[HexCoord] | None = None,
) -> list[NamedLandmass]:
    rng = build_seeded_rng(seed, "landmasses")
    used_names: set[str] = set()
    named_landmasses: list[NamedLandmass] = []

    for geoform in sorted(geoforms, key=lambda current: current.size, reverse=True):
        if geoform.type not in LAND_GEOFORM_TYPES or geoform.size <= 0:
            continue

        coords = tuple(
            sorted(
                (hex_tile.x, hex_tile.y)
                for hex_tile in geoform.hexes
                if visible_coords is None or (hex_tile.x, hex_tile.y) in visible_coords
            )
        )
        if not coords:
            continue

        name = generate_landmass_name(rng, geoform.type, used_names)
        setattr(geoform, "display_name", name)

        named_landmasses.append(
            NamedLandmass(
                id=geoform.id.hex,
                name=name,
                kind=_geoform_title(geoform.type),
                size=len(coords),
                tiles=coords,
            )
        )

    return named_landmasses


def apply_landmass_names(tiles: Mapping[HexCoord, "Tile"], landmasses: Iterable[NamedLandmass]) -> None:
    for landmass in landmasses:
        for coord in landmass.tiles:
            tile = tiles.get(coord)
            if tile is None:
                continue

            setattr(tile, "landmass_id", landmass.id)
            setattr(tile, "landmass_name", landmass.name)
            setattr(tile, "landmass_type", landmass.kind)
            setattr(tile, "landmass_size", landmass.size)
