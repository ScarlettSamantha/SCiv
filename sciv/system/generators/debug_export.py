import gzip
import math
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, cast
from uuid import UUID

import numpy as np
import orjson as json

from helpers.paths import PathsHelper
from system.generators.dynamic_worlds.biomes import build_named_biome_regions
from system.generators.dynamic_worlds.landmasses import build_named_landmasses
from system.generators.dynamic_worlds.rivers import build_named_rivers

if TYPE_CHECKING:
    from system.generators.base import BaseGenerator
    from system.subsystems.hexgen.geoform import Geoform
    from system.subsystems.hexgen.hex import Hex
    from system.subsystems.hexgen.mapgen import MapGen
    from system.subsystems.hexgen.river import RiverSegment
    from system.subsystems.hexgen.territory import Territory

DEFAULT_EXPORT_DIR = Path("sciv") / "debugging" / "worldgen"
EXPORT_SCHEMA_VERSION = 1


def default_worldgen_export_dir() -> str:
    return DEFAULT_EXPORT_DIR.as_posix()


def resolve_worldgen_export_dir(configured_dir: str | None = None) -> Path:
    candidate = Path((configured_dir or default_worldgen_export_dir()).strip()).expanduser()
    if not candidate.is_absolute():
        repo_root = PathsHelper.get_base_path().parent
        candidate = (repo_root / candidate).resolve()
    candidate.mkdir(parents=True, exist_ok=True)
    return candidate


def write_worldgen_export(
    payload: Mapping[str, Any],
    *,
    export_dir: str | Path | None = None,
    file_stem: str | None = None,
) -> Path:
    target_dir = resolve_worldgen_export_dir(str(export_dir) if export_dir is not None else None)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    stem = file_stem or f"worldgen_{timestamp}"
    target_path = target_dir / f"{stem}.json.gz"

    serializable = json_compatible(dict(payload))
    with gzip.open(target_path, "wb") as fp:
        fp.write(json.dumps(serializable))

    return target_path


def build_generator_export_payload(
    generator: "BaseGenerator",
    *,
    runtime_tiles: Mapping[str, Any] | None = None,
    source: str = "runtime",
    extra_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    mapgen = getattr(generator, "hexgen_map", None)
    if mapgen is None:
        raise ValueError("Generator does not expose a raw hexgen map for export.")

    config = getattr(generator, "config", None)
    requested_width = int(getattr(config, "width", getattr(mapgen.hex_grid, "size", 0)))
    requested_height = int(getattr(config, "height", getattr(mapgen.hex_grid, "size", 0)))
    seed = getattr(generator, "seed", getattr(config, "seed", None))

    return build_raw_world_payload(
        mapgen=mapgen,
        generator_name=str(getattr(generator, "NAME", generator.__class__.__name__)),
        generator_class=f"{generator.__class__.__module__}.{generator.__class__.__name__}",
        requested_width=requested_width,
        requested_height=requested_height,
        seed=seed,
        setup_options=getattr(generator, "setup_options", {}),
        map_params=getattr(generator, "map_params", {}),
        source=source,
        world_generation_stats=getattr(generator, "world_generation_stats", {}),
        legacy_debug_dump=getattr(generator, "debug_dump_data", {}),
        runtime_tiles=runtime_tiles,
        extra_meta=extra_meta,
    )


def build_raw_world_payload(
    *,
    mapgen: "MapGen",
    generator_name: str,
    generator_class: str,
    requested_width: int,
    requested_height: int,
    seed: int | None,
    setup_options: Mapping[str, Any] | None = None,
    map_params: Mapping[str, Any] | None = None,
    source: str,
    world_generation_stats: Mapping[str, Any] | None = None,
    legacy_debug_dump: Mapping[str, Any] | None = None,
    runtime_tiles: Mapping[str, Any] | None = None,
    extra_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    visible_bounds = (requested_height, requested_width)
    named_regions = _build_named_regions(mapgen=mapgen, seed=seed)
    rivers = _serialize_rivers(mapgen.rivers_sources)
    river_index = _build_river_hex_index(rivers)

    payload: dict[str, Any] = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "exported_at": datetime.now().isoformat(),
        "source": source,
        "generator": {
            "name": generator_name,
            "class": generator_class,
            "seed": seed,
            "setup_options": json_compatible(dict(setup_options or {})),
            "map_params": json_compatible(dict(map_params or {})),
        },
        "dimensions": {
            "requested": {
                "width": requested_width,
                "height": requested_height,
            },
            "raw_grid_size": int(mapgen.hex_grid.size),
            "visible_bounds": {
                "max_x_exclusive": int(visible_bounds[0]),
                "max_y_exclusive": int(visible_bounds[1]),
            },
        },
        "summary": _build_summary(mapgen=mapgen, river_exports=rivers, visible_bounds=visible_bounds),
        "raw": {
            "heightmap": {
                "average_height": int(mapgen.heightmap.average_height),
                "highest_height": int(mapgen.heightmap.highest_height),
                "lowest_height": int(mapgen.heightmap.lowest_height),
                "sealevel": float(mapgen.heightmap.sealevel),
                "grid": json_compatible(mapgen.heightmap.grid),
            },
            "hexes": [
                _serialize_hex(hex_tile, river_index=river_index, visible_bounds=visible_bounds)
                for hex_tile in sorted(mapgen.hex_grid.hexes, key=lambda current: (current.x, current.y))
            ],
            "geoforms": [
                _serialize_geoform(geoform)
                for geoform in sorted(mapgen.geoforms, key=lambda current: (current.size, current.id.hex), reverse=True)
            ],
            "territories": [
                _serialize_territory(territory)
                for territory in sorted(mapgen.territories, key=lambda current: current.id)
            ],
            "rivers": rivers,
            "named_regions": named_regions,
        },
    }

    if world_generation_stats:
        payload["world_generation_stats"] = json_compatible(dict(world_generation_stats))

    if legacy_debug_dump:
        payload["legacy_debug_dump"] = json_compatible(dict(legacy_debug_dump))

    if runtime_tiles is not None:
        payload["runtime"] = {
            "tile_count": len(runtime_tiles),
            "tiles": json_compatible(dict(runtime_tiles)),
        }

    if extra_meta:
        payload["meta"] = json_compatible(dict(extra_meta))

    return payload


def json_compatible(value: Any) -> Any:
    if isinstance(value, Mapping):
        mapping_value = cast(Mapping[object, object], value)
        return {str(key): json_compatible(val) for key, val in mapping_value.items()}

    if isinstance(value, np.ndarray):
        return value.tolist()

    if isinstance(value, np.generic):
        return cast(Any, value.item())

    if isinstance(value, (list, tuple)):
        sequence_value = cast(list[object] | tuple[object, ...], value)
        return [json_compatible(item) for item in sequence_value]

    if isinstance(value, set):
        set_value = cast(set[object], value)
        return [json_compatible(item) for item in sorted(set_value, key=repr)]

    if isinstance(value, UUID):
        return value.hex

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, Enum):
        title = getattr(value, "title", None)
        if title is not None:
            return {
                "key": value.name,
                "title": str(title),
            }
        return value.name

    if isinstance(value, float) and not math.isfinite(value):
        return None

    return value


def _coerce_int(value: object) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _coerce_coord_pair(value: object) -> tuple[int, int] | None:
    if not isinstance(value, (list, tuple)):
        return None

    sequence_value = cast(list[object] | tuple[object, ...], value)
    if len(sequence_value) != 2:
        return None

    x = _coerce_int(sequence_value[0])
    y = _coerce_int(sequence_value[1])
    if x is None or y is None:
        return None

    return (x, y)


def _build_named_regions(mapgen: "MapGen", seed: int | None) -> dict[str, list[dict[str, Any]]]:
    visible_coords = {(hex_tile.x, hex_tile.y) for hex_tile in mapgen.hex_grid.hexes}

    landmasses = build_named_landmasses(mapgen.geoforms, seed=seed, visible_coords=visible_coords)
    biome_regions = build_named_biome_regions(mapgen.hex_grid, seed=seed, visible_coords=visible_coords)
    rivers = build_named_rivers(mapgen.rivers_sources, seed=seed, visible_coords=visible_coords)

    return {
        "landmasses": [_serialize_named_region(region) for region in landmasses],
        "biome_regions": [_serialize_named_region(region) for region in biome_regions],
        "rivers": [_serialize_named_region(region) for region in rivers],
    }


def _serialize_named_region(region: Any) -> dict[str, Any]:
    data = json_compatible(region.to_dict())
    if hasattr(region, "tiles"):
        data["tiles"] = json_compatible(getattr(region, "tiles"))
    return data


def _build_summary(
    *,
    mapgen: "MapGen",
    river_exports: list[dict[str, Any]],
    visible_bounds: tuple[int, int],
) -> dict[str, Any]:
    land_hexes = 0
    water_hexes = 0
    coast_land_hexes = 0
    coast_water_hexes = 0
    inland_land_hexes = 0
    biome_counts: dict[str, int] = {}
    geoform_counts: dict[str, int] = {}

    visible_land_hexes = 0
    visible_water_hexes = 0

    for hex_tile in mapgen.hex_grid.hexes:
        visible = _is_visible(hex_tile.x, hex_tile.y, visible_bounds)
        if hex_tile.is_land:
            land_hexes += 1
            if visible:
                visible_land_hexes += 1
        else:
            water_hexes += 1
            if visible:
                visible_water_hexes += 1

        if hex_tile.is_coast_land:
            coast_land_hexes += 1
        if hex_tile.is_coast_water:
            coast_water_hexes += 1
        if hex_tile.is_inland:
            inland_land_hexes += 1

        biome_counts[hex_tile.biome.name] = biome_counts.get(hex_tile.biome.name, 0) + 1

    for geoform in mapgen.geoforms:
        geoform_counts[geoform.type.name] = geoform_counts.get(geoform.type.name, 0) + 1

    return {
        "hexes": {
            "land": land_hexes,
            "water": water_hexes,
            "coast_land": coast_land_hexes,
            "coast_water": coast_water_hexes,
            "inland_land": inland_land_hexes,
            "visible_land": visible_land_hexes,
            "visible_water": visible_water_hexes,
        },
        "heightmap": {
            "average_height": int(mapgen.heightmap.average_height),
            "highest_height": int(mapgen.heightmap.highest_height),
            "lowest_height": int(mapgen.heightmap.lowest_height),
            "sealevel": float(mapgen.heightmap.sealevel),
        },
        "geoforms": geoform_counts,
        "biomes": biome_counts,
        "territory_count": len(mapgen.territories),
        "river_count": len(river_exports),
        "river_segment_count": sum(int(river.get("length", 0)) for river in river_exports),
    }


def _serialize_hex(
    hex_tile: "Hex",
    *,
    river_index: Mapping[tuple[int, int], list[dict[str, Any]]],
    visible_bounds: tuple[int, int],
) -> dict[str, Any]:
    geoform = getattr(hex_tile, "geoform", None)
    territory = getattr(hex_tile, "territory", None)
    resource = hex_tile.get_gameplay_resource()

    return {
        "coord": [int(hex_tile.x), int(hex_tile.y)],
        "key": _coord_key(hex_tile.x, hex_tile.y),
        "visible_in_runtime": _is_visible(hex_tile.x, hex_tile.y, visible_bounds),
        "altitude": round(float(hex_tile.altitude), 3),
        "base_temperature": round(float(hex_tile.base_temperature[0]), 3),
        "temperature": round(float(hex_tile.temperature[0]), 3),
        "moisture": round(float(hex_tile.moisture), 3),
        "distance_to_water": round(float(getattr(hex_tile, "distance", 0.0)), 3),
        "latitude": round(float(hex_tile.latitude), 3),
        "latitude_ratio": round(float(hex_tile.latitude_ratio), 5),
        "hemisphere": hex_tile.hemisphere.name,
        "zone": hex_tile.zone.name,
        "type": hex_tile.type.name,
        "is_land": bool(hex_tile.is_land),
        "is_water": bool(hex_tile.is_water),
        "is_inland": bool(hex_tile.is_inland),
        "is_coast_land": bool(hex_tile.is_coast_land),
        "is_coast_water": bool(hex_tile.is_coast_water),
        "terrain": hex_tile.terrain or None,
        "biome": {
            "key": hex_tile.biome.name,
            "title": str(hex_tile.biome.title),
            "id": int(hex_tile.biome.id),
        },
        "geoform": None
        if geoform is None
        else {
            "id": geoform.id.hex,
            "type": geoform.type.name,
            "title": str(geoform.type.title),
            "size": int(geoform.size),
        },
        "territory_id": None if territory is None else int(territory.id),
        "features": sorted(feature.name for feature in hex_tile.features),
        "resource": getattr(resource, "key", getattr(resource, "__name__", None)) if resource is not None else None,
        "neighbors": [[int(neighbor.x), int(neighbor.y)] for _, neighbor in hex_tile.neighbors],
        "river_segments": json_compatible(river_index.get((hex_tile.x, hex_tile.y), [])),
    }


def _serialize_geoform(geoform: "Geoform") -> dict[str, Any]:
    hexes = sorted((hex_tile.x, hex_tile.y) for hex_tile in geoform.hexes)
    center_x = round(sum(coord[0] for coord in hexes) / max(1, len(hexes)), 3)
    center_y = round(sum(coord[1] for coord in hexes) / max(1, len(hexes)), 3)

    return {
        "id": geoform.id.hex,
        "type": geoform.type.name,
        "title": str(geoform.type.title),
        "size": int(geoform.size),
        "center": [center_x, center_y],
        "neighbors": sorted(neighbor.id.hex for neighbor in geoform.neighbors),
        "hexes": json_compatible(hexes),
    }


def _serialize_territory(territory: "Territory") -> dict[str, Any]:
    biomes: list[dict[str, str | int]] = []
    for entry in cast(list[Mapping[str, object]], territory.biomes):
        biome = entry.get("biome")
        if biome is None:
            continue

        biome_name = getattr(biome, "name", None)
        if not isinstance(biome_name, str):
            continue

        count = _coerce_int(entry.get("count", 0)) or 0

        biomes.append(
            {
                "key": biome_name,
                "title": str(getattr(biome, "title", biome_name)),
                "count": count,
            }
        )

    return {
        "id": int(territory.id),
        "main": [int(territory.main.x), int(territory.main.y)],
        "size": int(territory.size),
        "landlocked": bool(territory.landlocked),
        "avg_temp": float(territory.avg_temp()),
        "avg_moisture": float(territory.avg_moisture),
        "color": json_compatible(list(territory.color) if territory.color is not None else []),
        "neighbors": sorted(neighbor.id for neighbor in territory.neighbors),
        "groups": json_compatible(territory.groups),
        "biomes": biomes,
        "hexes": json_compatible(sorted((member.x, member.y) for member in territory.members)),
    }


def _serialize_rivers(river_sources: list["RiverSegment"]) -> list[dict[str, Any]]:
    exports: list[dict[str, Any]] = []

    for river_source in sorted(river_sources, key=lambda current: current.size, reverse=True):
        network_id = getattr(river_source, "network_id", river_source.id.hex)
        segments: list[dict[str, Any]] = []
        current = river_source
        while current is not None:
            edge_payload = None
            try:
                edge = current.edge
                edge_payload = {
                    "side": str(edge.side),
                    "between": [
                        [int(edge.one.x), int(edge.one.y)],
                        [int(edge.two.x), int(edge.two.y)],
                    ],
                    "up": [int(edge.up.x), int(edge.up.y)],
                    "down": [int(edge.down.x), int(edge.down.y)],
                    "delta": round(float(edge.delta), 3),
                    "is_coast": bool(edge.is_coast),
                    "is_river": bool(edge.is_river),
                    "direction": getattr(getattr(edge, "direction", None), "name", None),
                }
            except Exception:
                edge_payload = None

            segments.append(
                {
                    "coord": [int(current.x), int(current.y)],
                    "side": current.side.name,
                    "is_source": bool(current.is_source),
                    "edge": edge_payload,
                }
            )
            current = current.next

        source = segments[0]["coord"] if segments else None
        mouth = None
        if segments and segments[-1].get("edge") is not None:
            edge = segments[-1]["edge"]
            edge_mapping = cast(Mapping[str, object], edge) if isinstance(edge, dict) else None
            mouth = edge_mapping.get("down") if edge_mapping is not None else None

        exports.append(
            {
                "id": river_source.id.hex,
                "network_id": network_id,
                "branch_kind": getattr(river_source, "branch_kind", None),
                "display_name": getattr(river_source, "display_name", None),
                "length": len(segments),
                "source": source,
                "mouth": mouth,
                "segments": segments,
            }
        )

    return exports


def _build_river_hex_index(river_exports: list[dict[str, Any]]) -> dict[tuple[int, int], list[dict[str, Any]]]:
    index: dict[tuple[int, int], list[dict[str, Any]]] = {}

    for river in river_exports:
        river_id = str(river.get("network_id") or river.get("id", ""))
        river_name = river.get("display_name")
        branch_kind = river.get("branch_kind")
        segments = river.get("segments")
        if not isinstance(segments, list):
            continue

        segment_list = cast(list[object], segments)
        for segment in segment_list:
            if not isinstance(segment, Mapping):
                continue

            segment_data = cast(Mapping[str, object], segment)
            key = _coerce_coord_pair(segment_data.get("coord"))
            if key is None:
                continue

            index.setdefault(key, []).append(
                {
                    "river_id": river_id,
                    "river_name": river_name,
                    "branch_kind": branch_kind,
                    "side": segment_data.get("side"),
                    "is_source": bool(segment_data.get("is_source", False)),
                }
            )

    return index


def _coord_key(x: int, y: int) -> str:
    return f"{x},{y}"


def _is_visible(x: int, y: int, visible_bounds: tuple[int, int]) -> bool:
    return 0 <= x < visible_bounds[0] and 0 <= y < visible_bounds[1]
