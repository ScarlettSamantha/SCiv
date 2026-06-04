import gzip
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


type HexCoord = tuple[int, int]
type JsonDict = dict[str, Any]


_TERRAIN_DISPLAY_NAMES: dict[str, str] = {
    "coast": "Coast",
    "lake": "Lake",
    "sea": "Sea",
    "seaice": "Sea Ice",
    "ocean": "Ocean",
    "mountain": "Mountain",
    "mountainsnow": "Mountain Snow",
    "volcano": "Volcano",
    "hillssnow": "Hills Snow",
    "hillsdesert": "Hills Desert",
    "hillsgrassland": "Hills Grassland",
    "hillsforest": "Hills Forest",
    "hillstundra": "Hills Tundra",
    "flatlightjungle": "Flat Light Jungle",
    "flatjungle": "Flat Jungle",
    "flatgrass": "Flat Grass",
    "flatdesert": "Flat Desert",
    "flatforest": "Flat Forest",
    "flatheavyforest": "Flat Heavy Forest",
    "flatpineforest": "Flat Pine Forest",
    "flatsavanna": "Flat Savanna",
    "flatscrubland": "Flat Scrubland",
    "flatice": "Flat Ice",
    "flattundrasnow": "Flat Tundra Snow",
    "flattundra": "Flat Tundra",
}


def resource_display_name(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    if not normalized:
        return None

    leaf_name = normalized.rsplit(".", 1)[-1]
    return leaf_name.replace("_", " ").replace("-", " ").strip().title()


def resource_display_category(value: str | None) -> str | None:
    if value is None:
        return None

    parts = [part.strip() for part in value.split(".") if part.strip()]
    if len(parts) < 2:
        return None

    category = parts[-2]
    return category.replace("_", " ").replace("-", " ").strip().title()


def resource_display_text(value: str | None) -> str | None:
    name = resource_display_name(value)
    if name is None:
        return None

    category = resource_display_category(value)
    if category is None:
        return name

    return f"{name} ({category})"


@dataclass(frozen=True, slots=True)
class HexRecord:
    coord: HexCoord
    visible_in_runtime: bool
    altitude: float
    moisture: float
    temperature: float
    terrain: str | None
    biome_key: str
    biome_title: str
    geoform_type: str | None
    geoform_title: str | None
    territory_id: int | None
    territory_name: str | None
    is_land: bool
    is_water: bool
    is_inland: bool
    is_coast_land: bool
    is_coast_water: bool
    features: tuple[str, ...]
    river_segments: tuple[JsonDict, ...]
    raw: JsonDict


@dataclass(frozen=True, slots=True)
class NamedRegionRecord:
    kind: str
    name: str
    anchor: HexCoord | None
    tiles: tuple[HexCoord, ...]
    raw: JsonDict


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    file_path: Path
    label: str
    seed: int | None
    generator: str
    summary: JsonDict


@dataclass(frozen=True, slots=True)
class WorldgenDump:
    path: Path
    title: str
    generator_name: str
    seed: int | None
    requested_width: int
    requested_height: int
    raw_grid_size: int
    hexes: tuple[HexRecord, ...]
    hexes_by_coord: dict[HexCoord, HexRecord]
    named_regions: dict[str, tuple[NamedRegionRecord, ...]]
    territory_names_by_id: dict[int, str]
    rivers: tuple[JsonDict, ...]
    summary: JsonDict
    runtime_tiles_by_coord: dict[HexCoord, JsonDict]
    raw_payload: JsonDict
    altitude_range: tuple[float, float]
    moisture_range: tuple[float, float]


def load_json_document(path: Path) -> JsonDict:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as fp:
            return json.load(fp)

    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def load_manifest(path: Path) -> tuple[ManifestEntry, ...] | None:
    payload = load_json_document(path)
    worlds = payload.get("worlds")
    if not isinstance(worlds, list) or "raw" in payload:
        return None

    entries: list[ManifestEntry] = []
    for index, world in enumerate(worlds, start=1):
        if not isinstance(world, dict):
            continue

        raw_file = world.get("file")
        if not isinstance(raw_file, str) or not raw_file.strip():
            continue

        file_path = Path(raw_file).expanduser()
        if not file_path.is_absolute():
            file_path = (path.parent / file_path).resolve()

        seed = world.get("seed") if isinstance(world.get("seed"), int) else None
        generator = str(world.get("generator", "World"))
        summary = world.get("summary") if isinstance(world.get("summary"), dict) else {}
        label = f"{index:02d} • {generator}"
        if seed is not None:
            label += f" • seed {seed}"
        label += f" • {file_path.name}"

        entries.append(
            ManifestEntry(
                file_path=file_path,
                label=label,
                seed=seed,
                generator=generator,
                summary=dict(summary),
            )
        )

    return tuple(entries)


def load_worldgen_dump(path: Path) -> WorldgenDump:
    payload = load_json_document(path)
    return load_worldgen_payload(payload, path=path)


def load_worldgen_payload(payload: JsonDict, *, path: Path | None = None) -> WorldgenDump:
    raw = payload.get("raw") if isinstance(payload.get("raw"), dict) else {}
    hex_payloads = raw.get("hexes") if isinstance(raw.get("hexes"), list) else []
    named_region_payloads = raw.get("named_regions") if isinstance(raw.get("named_regions"), dict) else {}
    raw_territories = raw.get("territories") if isinstance(raw.get("territories"), list) else []

    territory_names_by_id: dict[int, str] = {}
    for raw_territory in raw_territories:
        if not isinstance(raw_territory, dict):
            continue

        territory_id = raw_territory.get("id")
        territory_name = _optional_str(raw_territory.get("name"))
        if isinstance(territory_id, int) and territory_name is not None:
            territory_names_by_id[territory_id] = territory_name

    hexes: list[HexRecord] = []
    hexes_by_coord: dict[HexCoord, HexRecord] = {}
    altitudes: list[float] = []
    moistures: list[float] = []

    for raw_hex in hex_payloads:
        if not isinstance(raw_hex, dict):
            continue

        coord = _coord_tuple(raw_hex.get("coord"))
        if coord is None:
            continue

        altitude = float(raw_hex.get("altitude", 0.0))
        moisture = float(raw_hex.get("moisture", 0.0))
        record = HexRecord(
            coord=coord,
            visible_in_runtime=bool(raw_hex.get("visible_in_runtime", False)),
            altitude=altitude,
            moisture=moisture,
            temperature=float(raw_hex.get("temperature", 0.0)),
            terrain=_optional_str(raw_hex.get("terrain")),
            biome_key=str(_dict_value(raw_hex.get("biome"), "key", "unknown")),
            biome_title=str(_dict_value(raw_hex.get("biome"), "title", "Unknown")),
            geoform_type=_optional_nested_str(raw_hex.get("geoform"), "type"),
            geoform_title=_optional_nested_str(raw_hex.get("geoform"), "title"),
            territory_id=raw_hex.get("territory_id") if isinstance(raw_hex.get("territory_id"), int) else None,
            territory_name=_optional_str(raw_hex.get("territory_name")),
            is_land=bool(raw_hex.get("is_land", False)),
            is_water=bool(raw_hex.get("is_water", False)),
            is_inland=bool(raw_hex.get("is_inland", False)),
            is_coast_land=bool(raw_hex.get("is_coast_land", False)),
            is_coast_water=bool(raw_hex.get("is_coast_water", False)),
            features=tuple(str(feature) for feature in raw_hex.get("features", []) if isinstance(feature, str)),
            river_segments=tuple(segment for segment in raw_hex.get("river_segments", []) if isinstance(segment, dict)),
            raw=dict(raw_hex),
        )
        hexes.append(record)
        hexes_by_coord[coord] = record
        altitudes.append(altitude)
        moistures.append(moisture)

    if "territories" not in named_region_payloads and raw_territories:
        named_region_payloads = dict(named_region_payloads)
        named_region_payloads["territories"] = [
            {
                "name": raw_territory.get("name") or f"Territory {raw_territory.get('id', '?')}",
                "anchor": raw_territory.get("main"),
                "tiles": raw_territory.get("hexes", []),
            }
            for raw_territory in raw_territories
            if isinstance(raw_territory, dict)
        ]

    named_regions: dict[str, tuple[NamedRegionRecord, ...]] = {}
    for kind, raw_regions in named_region_payloads.items():
        if not isinstance(raw_regions, list):
            continue

        parsed_regions: list[NamedRegionRecord] = []
        for raw_region in raw_regions:
            if not isinstance(raw_region, dict):
                continue
            tiles = tuple(coord for coord in (_coord_tuple(value) for value in raw_region.get("tiles", [])) if coord is not None)
            anchor = _coord_tuple(raw_region.get("anchor"))
            if anchor is None:
                anchor = _coord_tuple(raw_region.get("source"))
            if anchor is None and tiles:
                anchor = tiles[0]

            parsed_regions.append(
                NamedRegionRecord(
                    kind=str(kind),
                    name=str(raw_region.get("name", "Unnamed")),
                    anchor=anchor,
                    tiles=tiles,
                    raw=dict(raw_region),
                )
            )
        named_regions[str(kind)] = tuple(parsed_regions)

    dimensions = payload.get("dimensions") if isinstance(payload.get("dimensions"), dict) else {}
    requested = dimensions.get("requested") if isinstance(dimensions.get("requested"), dict) else {}
    runtime_payload = payload.get("runtime") if isinstance(payload.get("runtime"), dict) else {}
    runtime_tiles = runtime_payload.get("tiles") if isinstance(runtime_payload.get("tiles"), dict) else {}

    runtime_tiles_by_coord: dict[HexCoord, JsonDict] = {}
    for key, value in runtime_tiles.items():
        coord = _coord_from_key(key)
        if coord is None or not isinstance(value, dict):
            continue
        runtime_tiles_by_coord[coord] = dict(value)

    generator = payload.get("generator") if isinstance(payload.get("generator"), dict) else {}
    generator_name = str(generator.get("name", "Worldgen Dump"))
    seed = generator.get("seed") if isinstance(generator.get("seed"), int) else None
    title = generator_name if seed is None else f"{generator_name} • seed {seed}"

    altitude_range = (min(altitudes) if altitudes else 0.0, max(altitudes) if altitudes else 0.0)
    moisture_range = (min(moistures) if moistures else 0.0, max(moistures) if moistures else 0.0)

    return WorldgenDump(
        path=path or Path("<generated>"),
        title=title,
        generator_name=generator_name,
        seed=seed,
        requested_width=int(requested.get("width", 0)),
        requested_height=int(requested.get("height", 0)),
        raw_grid_size=int(dimensions.get("raw_grid_size", 0)),
        hexes=tuple(hexes),
        hexes_by_coord=hexes_by_coord,
        named_regions=named_regions,
        territory_names_by_id=territory_names_by_id,
        rivers=tuple(river for river in raw.get("rivers", []) if isinstance(river, dict)),
        summary=dict(payload.get("summary", {})) if isinstance(payload.get("summary"), dict) else {},
        runtime_tiles_by_coord=runtime_tiles_by_coord,
        raw_payload=dict(payload),
        altitude_range=altitude_range,
        moisture_range=moisture_range,
    )


def format_dump_summary(dump: WorldgenDump) -> str:
    hexes = dump.summary.get("hexes", {}) if isinstance(dump.summary.get("hexes"), dict) else {}
    river_networks = {
        str(river.get("network_id") or river.get("id") or "")
        for river in dump.rivers
        if isinstance(river, dict) and (river.get("network_id") or river.get("id"))
    }
    lines = [
        dump.title,
        f"File: {dump.path}",
        f"Requested size: {dump.requested_width} × {dump.requested_height}",
        f"Raw grid size: {dump.raw_grid_size}",
        f"Hexes: land={hexes.get('land', 0)} water={hexes.get('water', 0)} visible_land={hexes.get('visible_land', 0)}",
        f"Rivers: {dump.summary.get('river_count', 0)} chains / {len(river_networks)} networks / {dump.summary.get('river_segment_count', 0)} segments",
        f"Territories: {dump.summary.get('territory_count', 0)}",
        f"Runtime tiles present: {'yes' if dump.runtime_tiles_by_coord else 'no'}",
    ]
    return "\n".join(lines)


def describe_hex_classification(record: HexRecord, runtime_tile: JsonDict | None = None) -> str:
    raw_terrain_label = terrain_display_name(record.terrain)
    runtime_terrain_label = terrain_display_name(_optional_str(runtime_tile.get("terrain")) if runtime_tile is not None else None)

    if record.is_water:
        if raw_terrain_label == "Sea Ice" or runtime_terrain_label == "Sea Ice":
            return "Sea Ice"
        if raw_terrain_label == "Lake" or _runtime_flag(runtime_tile, "is_lake") or record.geoform_type == "lake":
            return "Lake"
        if raw_terrain_label == "Coast" or _runtime_flag(runtime_tile, "is_coast") or record.is_coast_water:
            return "Coast"
        if record.geoform_title:
            return record.geoform_title
        if raw_terrain_label is not None:
            return raw_terrain_label
        if runtime_terrain_label is not None:
            return runtime_terrain_label
        return "Water"

    if raw_terrain_label is not None:
        return raw_terrain_label
    if runtime_terrain_label is not None:
        return runtime_terrain_label
    return record.biome_title


def format_hex_tooltip(dump: WorldgenDump, coord: HexCoord) -> str:
    record = dump.hexes_by_coord[coord]
    runtime_tile = dump.runtime_tiles_by_coord.get(coord)
    classification = describe_hex_classification(record, runtime_tile)
    lines = [f"{record.coord[0]}, {record.coord[1]} • {classification}"]

    resource_text = resource_display_text(_optional_str(runtime_tile.get("resource")) if runtime_tile is not None else None)
    if resource_text is not None:
        lines.append(f"Resource: {resource_text}")

    if classification != record.biome_title:
        lines.append(f"Raw climate biome: {record.biome_title}")

    return "\n".join(lines)


def format_hex_details(dump: WorldgenDump, coord: HexCoord) -> str:
    record = dump.hexes_by_coord[coord]
    runtime_tile = dump.runtime_tiles_by_coord.get(coord)
    runtime_terrain_key = _optional_str(runtime_tile.get("terrain")) if runtime_tile is not None else None
    runtime_terrain_label = terrain_display_name(runtime_terrain_key)
    runtime_resource_text = resource_display_text(_optional_str(runtime_tile.get("resource")) if runtime_tile is not None else None)
    river_network_ids = river_network_ids_for_record(record)
    river_branch_kinds = river_branch_kinds_for_record(record)
    lines = [
        f"Coord: {record.coord[0]}, {record.coord[1]}",
        f"Visible in runtime: {'yes' if record.visible_in_runtime else 'no'}",
        f"Altitude: {record.altitude:.2f}",
        f"Moisture: {record.moisture:.2f}",
        f"Temperature: {record.temperature:.2f}",
        f"Classification: {describe_hex_classification(record, runtime_tile)}",
        f"Raw climate biome: {record.biome_title} ({record.biome_key})",
        f"Geoform: {record.geoform_title or 'None'}",
        f"Territory: {_territory_display_name(dump, record)}",
        f"Type: {'land' if record.is_land else 'water'}",
        f"Features: {', '.join(record.features) if record.features else 'None'}",
        f"River role: {river_role_label(record)}",
        f"River segments: {len(record.river_segments)}",
    ]

    if record.river_segments:
        lines.extend(
            [
                f"River networks: {len(river_network_ids)}",
                f"River branch types: {', '.join(river_branch_kinds) if river_branch_kinds else 'Main channel only'}",
            ]
        )

    if runtime_tile is not None:
        lines.extend(
            [
                "",
                "Runtime tile:",
                f"  Terrain: {_format_runtime_terrain_text(runtime_terrain_key, runtime_terrain_label)}",
                f"  Resource: {runtime_resource_text or 'None'}",
                f"  Landmass: {runtime_tile.get('landmass_name', 'None')}",
                f"  Biome region: {runtime_tile.get('biome_region_name', 'None')}",
                f"  Primary river: {runtime_tile.get('primary_river_name') or 'None'}",
                f"  River names: {', '.join(runtime_tile.get('river_names', [])) if runtime_tile.get('river_names') else 'None'}",
            ]
        )

    return "\n".join(lines)


def river_network_ids_for_record(record: HexRecord) -> tuple[str, ...]:
    network_ids = {
        str(segment.get("river_id", ""))
        for segment in record.river_segments
        if isinstance(segment.get("river_id"), str) and str(segment.get("river_id", "")).strip()
    }
    return tuple(sorted(network_ids))


def river_branch_kinds_for_record(record: HexRecord) -> tuple[str, ...]:
    branch_kinds = {
        str(segment.get("branch_kind", "")).replace("_", " ").strip().title()
        for segment in record.river_segments
        if isinstance(segment.get("branch_kind"), str) and str(segment.get("branch_kind", "")).strip()
    }
    return tuple(sorted(branch_kinds))


def river_role_label(record: HexRecord) -> str:
    if not record.river_segments:
        return "Water without river" if record.is_water else "Land without river"

    if record.is_water:
        return "River mouth"

    if any(bool(segment.get("is_source", False)) for segment in record.river_segments):
        return "Headwaters"

    if len(river_network_ids_for_record(record)) > 1:
        return "River confluence"

    branch_kinds = {kind.lower() for kind in river_branch_kinds_for_record(record)}
    if "distributary" in branch_kinds:
        return "River braid"
    if "connector" in branch_kinds:
        return "River connector"

    return "River channel"


def _territory_display_name(dump: WorldgenDump, record: HexRecord) -> str:
    if record.territory_id is None:
        return "None"

    territory_name = record.territory_name or dump.territory_names_by_id.get(record.territory_id)
    if territory_name is None:
        return f"Territory {record.territory_id}"

    return f"{territory_name} (ID {record.territory_id})"


def _coord_tuple(value: Any) -> HexCoord | None:
    if not isinstance(value, list | tuple) or len(value) != 2:
        return None
    first, second = value
    if not isinstance(first, int) or not isinstance(second, int):
        return None
    return int(first), int(second)


def _coord_from_key(key: Any) -> HexCoord | None:
    if not isinstance(key, str):
        return None
    parts = [part.strip() for part in key.split(",")]
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def _runtime_flag(runtime_tile: JsonDict | None, key: str) -> bool:
    if runtime_tile is None:
        return False
    return bool(runtime_tile.get(key, False))


def terrain_display_name(value: str | None) -> str | None:
    if value is None:
        return None

    key = value.strip().replace("_", "").replace("-", "").lower()
    if not key:
        return None

    return _TERRAIN_DISPLAY_NAMES.get(key, value.replace("_", " ").replace("-", " ").strip().title())


def _terrain_display_name(value: str | None) -> str | None:
    return terrain_display_name(value)


def _format_runtime_terrain_text(terrain_key: str | None, terrain_label: str | None) -> str:
    if terrain_key is None:
        return "None"
    if terrain_label is None:
        return terrain_key
    if terrain_label.lower() == terrain_key.lower():
        return terrain_label
    return f"{terrain_label} ({terrain_key})"


def _dict_value(value: Any, key: str, default: Any) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return default


def _optional_str(value: Any) -> str | None:
    return str(value) if isinstance(value, str) and value else None


def _optional_nested_str(value: Any, key: str) -> str | None:
    if not isinstance(value, dict):
        return None
    nested = value.get(key)
    return str(nested) if isinstance(nested, str) and nested else None
