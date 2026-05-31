#!/usr/bin/env python3
"""Shared offline world-generation helpers for export and preview tooling."""

import json
import os
import random
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]
SCIV_ROOT = REPO_ROOT / "sciv"

os.environ.setdefault("KIVY_NO_ARGS", "1")
if str(SCIV_ROOT) not in sys.path:
    sys.path.insert(0, str(SCIV_ROOT))

from system.generators.terrain_conversion import (
    adjust_water_levels as adjust_shared_water_levels,
    classify_visible_hexes,
    desertize_adjacent_tundra as desertize_shared_adjacent_tundra,
    promote_single_sea_between_coasts as promote_shared_single_sea_between_coasts,
)


type JsonDict = dict[str, Any]
type ChoiceList = tuple[tuple[str, str], ...]
type ProgressCallback = Callable[[int, int, str], None]


@dataclass(frozen=True, slots=True)
class OfflineOptionSpec:
    key: str
    label: str
    default: str
    choices: ChoiceList

    @property
    def allowed_values(self) -> set[str]:
        return {value for _, value in self.choices}

    def sanitize(self, raw_value: str | None) -> str:
        if raw_value in self.allowed_values:
            return raw_value
        return self.default


@dataclass(frozen=True, slots=True)
class OfflineGeneratorSpec:
    name: str
    description: str
    class_path: str
    options: tuple[OfflineOptionSpec, ...] = ()

    def sanitize_options(self, raw_options: dict[str, str]) -> dict[str, str]:
        sanitized: dict[str, str] = {}
        for option in self.options:
            sanitized[option.key] = option.sanitize(raw_options.get(option.key))
        return sanitized

    def default_options(self) -> dict[str, str]:
        return {option.key: option.default for option in self.options}


_BOOTSTRAPPED = False
_OFFLINE_GENERATORS: dict[str, OfflineGeneratorSpec] | None = None
_PROFILE_CHOICES: tuple[ChoiceList, ChoiceList] | None = None
_RIVER_CHOICES: tuple[ChoiceList, ChoiceList, ChoiceList, ChoiceList] | None = None
_OCEAN_CONNECTIVITY_CHOICES: ChoiceList | None = None

WORLD_AGE_CHOICES: ChoiceList = (
    ("Young", "young"),
    ("Standard", "standard"),
    ("Old", "old"),
)
LANDMASS_FALLBACK_CHOICES: ChoiceList = (
    ("Continents", "continents"),
    ("Pangaea", "pangaea"),
    ("Small Continents", "small_continents"),
    ("Archipelago", "archipelago"),
    ("Fractal", "fractal"),
)
BIOME_STYLE_FALLBACK_CHOICES: ChoiceList = (
    ("Balanced", "balanced"),
    ("Verdant", "verdant"),
    ("Arid", "arid"),
    ("Frigid", "frigid"),
)
TEMPERATURE_CHOICES: ChoiceList = (
    ("Cool", "cool"),
    ("Temperate", "temperate"),
    ("Hot", "hot"),
)
HUMIDITY_CHOICES: ChoiceList = (
    ("Arid", "arid"),
    ("Normal", "normal"),
    ("Wet", "wet"),
)
SEA_LEVEL_CHOICES: ChoiceList = (
    ("Low", "low"),
    ("Normal", "normal"),
    ("High", "high"),
)
OCEAN_CONNECTIVITY_FALLBACK_CHOICES: ChoiceList = (
    ("Natural", "natural"),
    ("Connected Main Oceans", "connected"),
)
RIVER_AMOUNT_FALLBACK_CHOICES: ChoiceList = (
    ("Sparse", "sparse"),
    ("Normal", "normal"),
    ("Plentiful", "plentiful"),
)
RIVER_LENGTH_FALLBACK_CHOICES: ChoiceList = (
    ("Short", "short"),
    ("Normal", "normal"),
    ("Long", "long"),
)
TRIBUTARY_FALLBACK_CHOICES: ChoiceList = (
    ("Few", "few"),
    ("Normal", "normal"),
    ("Many", "many"),
)
RIVER_NETWORK_FALLBACK_CHOICES: ChoiceList = (
    ("Simple", "simple"),
    ("Natural", "natural"),
    ("Braided", "braided"),
)
UNIQUE_GENERATOR_KEYS = ("civlike", "dynamic worlds")

_OFFLINE_RESOURCE_TERRAIN_CLASS_PATHS: dict[str, str] = {
    "Coast": "gameplay.terrain.coast.Coast",
    "FlatDesert": "gameplay.terrain.flat_desert.FlatDesert",
    "FlatForest": "gameplay.terrain.flat_forest.FlatForest",
    "FlatGrass": "gameplay.terrain.flat_grass.FlatGrass",
    "FlatHeavyForest": "gameplay.terrain.flat_heavy_forest.FlatHeavyForest",
    "FlatIce": "gameplay.terrain.flat_ice.FlatIce",
    "FlatJungle": "gameplay.terrain.flat_jungle.FlatJungle",
    "FlatLightJungle": "gameplay.terrain.flat_light_jungle.FlatLightJungle",
    "FlatPineForest": "gameplay.terrain.flat_pine_forest.FlatPineForest",
    "FlatSavanna": "gameplay.terrain.flat_savanna.FlatSavanna",
    "FlatScrubland": "gameplay.terrain.flat_scrubland.FlatScrubland",
    "FlatTundra": "gameplay.terrain.flat_tundra.FlatTundra",
    "FlatTundraSnow": "gameplay.terrain.flat_tundra_snow.FlatTundraSnow",
    "HillsDesert": "gameplay.terrain.hills_desert.HillsDesert",
    "HillsForest": "gameplay.terrain.hills_forest.HillsForest",
    "HillsGrassland": "gameplay.terrain.hills_grass.HillsGrass",
    "HillsSnow": "gameplay.terrain.hills_snow.HillsSnow",
    "HillsTundra": "gameplay.terrain.hills_tundra.HillsTundra",
    "Lake": "gameplay.terrain.lake.Lake",
    "Mountain": "gameplay.terrain.mountain.Mountain",
    "MountainSnow": "gameplay.terrain.mountain_snow.MountainSnow",
    "Sea": "gameplay.terrain.sea.Sea",
    "SeaIce": "gameplay.terrain.sea_ice.SeaIce",
    "Volcano": "gameplay.terrain.volcano.Volcano",
}

_OFFLINE_TERRAIN_INSTANCES: dict[str, Any] | None = None


@dataclass(slots=True, eq=False)
class _OfflineRuntimeTileProxy:
    x: int
    y: int
    is_water: bool
    is_coast: bool
    raw_hex: Any
    terrain: Any
    resources: Any
    passable: bool

    def get_terrain(self) -> Any:
        return self.terrain

    def add_resource(self, resource: Any) -> None:
        self.resources.add(resource)
        self.raw_hex.add_gameplay_resource(resource.__class__)

    def is_passable(self) -> bool:
        return self.passable

    def get_climbable(self) -> bool:
        return True


@dataclass(frozen=True, slots=True)
class _FallbackConfigManager:
    export_dir: str
    batch_count: int

    def get_world_generation_export_dir(self) -> str:
        return self.export_dir

    def get_world_generation_export_batch_count(self) -> int:
        return self.batch_count


@contextmanager
def _temporary_working_directory(path: Path) -> Iterator[None]:
    original_path = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(original_path)


def _load_profile_choices() -> tuple[ChoiceList, ChoiceList]:
    global _PROFILE_CHOICES
    if _PROFILE_CHOICES is not None:
        return _PROFILE_CHOICES

    try:
        from system.generators.dynamic_worlds.profiles import biome_style_choices, landmass_choices

        _PROFILE_CHOICES = (landmass_choices(), biome_style_choices())
    except Exception:
        _PROFILE_CHOICES = (LANDMASS_FALLBACK_CHOICES, BIOME_STYLE_FALLBACK_CHOICES)

    return _PROFILE_CHOICES


def _load_river_choices() -> tuple[ChoiceList, ChoiceList, ChoiceList, ChoiceList]:
    global _RIVER_CHOICES
    if _RIVER_CHOICES is not None:
        return _RIVER_CHOICES

    try:
        from system.generators.dynamic_worlds.profiles import (
            river_amount_choices,
            river_length_choices,
            river_network_choices,
            tributary_choices,
        )

        _RIVER_CHOICES = (
            river_amount_choices(),
            river_length_choices(),
            tributary_choices(),
            river_network_choices(),
        )
    except Exception:
        _RIVER_CHOICES = (
            RIVER_AMOUNT_FALLBACK_CHOICES,
            RIVER_LENGTH_FALLBACK_CHOICES,
            TRIBUTARY_FALLBACK_CHOICES,
            RIVER_NETWORK_FALLBACK_CHOICES,
        )

    return _RIVER_CHOICES


def _load_ocean_connectivity_choices() -> ChoiceList:
    global _OCEAN_CONNECTIVITY_CHOICES
    if _OCEAN_CONNECTIVITY_CHOICES is not None:
        return _OCEAN_CONNECTIVITY_CHOICES

    try:
        from system.generators.dynamic_worlds.profiles import ocean_connectivity_choices

        _OCEAN_CONNECTIVITY_CHOICES = ocean_connectivity_choices()
    except Exception:
        _OCEAN_CONNECTIVITY_CHOICES = OCEAN_CONNECTIVITY_FALLBACK_CHOICES

    return _OCEAN_CONNECTIVITY_CHOICES


def get_offline_generators() -> dict[str, OfflineGeneratorSpec]:
    global _OFFLINE_GENERATORS
    if _OFFLINE_GENERATORS is not None:
        return _OFFLINE_GENERATORS

    landmass_choices, biome_style_choices = _load_profile_choices()
    river_amount_choices, river_length_choices, tributary_choices, river_network_choices = _load_river_choices()
    ocean_connectivity_choices = _load_ocean_connectivity_choices()
    dynamic_options = (
        OfflineOptionSpec(
            key="map_script",
            label="Map script",
            default="continents",
            choices=landmass_choices,
        ),
        OfflineOptionSpec(
            key="biome_style",
            label="Biome style",
            default="balanced",
            choices=biome_style_choices,
        ),
        OfflineOptionSpec(
            key="world_age",
            label="World age",
            default="standard",
            choices=WORLD_AGE_CHOICES,
        ),
        OfflineOptionSpec(
            key="temperature",
            label="Temperature",
            default="temperate",
            choices=TEMPERATURE_CHOICES,
        ),
        OfflineOptionSpec(
            key="humidity",
            label="Humidity",
            default="normal",
            choices=HUMIDITY_CHOICES,
        ),
        OfflineOptionSpec(
            key="sea_level",
            label="Sea level",
            default="normal",
            choices=SEA_LEVEL_CHOICES,
        ),
        OfflineOptionSpec(
            key="ocean_connectivity",
            label="Ocean connectivity",
            default="natural",
            choices=ocean_connectivity_choices,
        ),
        OfflineOptionSpec(
            key="river_amount",
            label="River amount",
            default="normal",
            choices=river_amount_choices,
        ),
        OfflineOptionSpec(
            key="river_length",
            label="River length",
            default="normal",
            choices=river_length_choices,
        ),
        OfflineOptionSpec(
            key="tributaries",
            label="Tributaries",
            default="normal",
            choices=tributary_choices,
        ),
        OfflineOptionSpec(
            key="river_network",
            label="River networks",
            default="natural",
            choices=river_network_choices,
        ),
    )

    basic_spec = OfflineGeneratorSpec(
        name="CivLike",
        description="Generates a hex-based map using HexGen.",
        class_path="system.generators.basic.Basic",
    )
    dynamic_spec = OfflineGeneratorSpec(
        name="Dynamic Worlds",
        description="Preset-driven generator with configurable landmass and climate variety.",
        class_path="system.generators.dynamic.Dynamic",
        options=dynamic_options,
    )

    _OFFLINE_GENERATORS = {
        "civlike": basic_spec,
        "basic": basic_spec,
        "dynamic worlds": dynamic_spec,
        "dynamic": dynamic_spec,
    }
    return _OFFLINE_GENERATORS


def list_offline_generators() -> tuple[OfflineGeneratorSpec, ...]:
    generators = get_offline_generators()
    return tuple(generators[key] for key in UNIQUE_GENERATOR_KEYS)


def resolve_offline_generator(name: str) -> OfflineGeneratorSpec:
    lookup = name.strip().lower()
    generators = get_offline_generators()
    if lookup not in generators:
        supported = ", ".join(spec.name for spec in list_offline_generators())
        raise ValueError(f"Unsupported generator '{name}'. Supported values: {supported}.")
    return generators[lookup]


def generate_random_seed() -> int:
    return random.randint(0, 2**31 - 1)


def ensure_offline_worldgen_bootstrap() -> None:
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return

    with _temporary_working_directory(SCIV_ROOT):
        from managers.config import ConfigManager
        from managers.log import LogManager

        try:
            ConfigManager.get_singleton_instance()
        except ValueError:
            ConfigManager()

        try:
            LogManager.get_singleton_instance()
        except ValueError:
            LogManager(debug_mode=False)

    _BOOTSTRAPPED = True


def get_config_manager() -> Any:
    try:
        ensure_offline_worldgen_bootstrap()

        from managers.config import ConfigManager

        return ConfigManager.get_singleton_instance()
    except Exception:
        return _load_fallback_config_manager()


def json_ready(data: dict[str, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in data.items()}


def _report_progress(
    progress_callback: ProgressCallback | None,
    *,
    step: int,
    total: int,
    message: str,
) -> None:
    if progress_callback is None:
        return

    progress_callback(step, total, message)


def _prepare_offline_hexes_for_export(
    mapgen: Any,
    generator_spec: OfflineGeneratorSpec,
    *,
    width: int,
    height: int,
    options: dict[str, Any],
) -> None:
    raw_grid = mapgen.hex_grid.grid

    classify_visible_hexes(raw_grid, width=width, height=height)
    adjust_shared_water_levels(raw_grid, width=width, height=height)
    promote_shared_single_sea_between_coasts(raw_grid, width=width, height=height)

    if generator_spec.name == "Dynamic Worlds":
        from system.generators.dynamic_worlds.coastline import apply_scripted_coastline_polish

        apply_scripted_coastline_polish(
            mapgen.hex_grid,
            str(options.get("map_script", "continents")),
        )

    desertize_shared_adjacent_tundra(raw_grid, width=width, height=height)


def _terrain_name_to_runtime_key(terrain_name: str | None) -> str | None:
    if terrain_name is None or not terrain_name:
        return None
    return terrain_name.lower().replace("_", "-")


def _load_offline_terrain_instances() -> dict[str, Any]:
    global _OFFLINE_TERRAIN_INSTANCES
    if _OFFLINE_TERRAIN_INSTANCES is not None:
        return _OFFLINE_TERRAIN_INSTANCES

    ensure_offline_worldgen_bootstrap()

    terrain_instances: dict[str, Any] = {}
    with _temporary_working_directory(SCIV_ROOT):
        for terrain_name, class_path in _OFFLINE_RESOURCE_TERRAIN_CLASS_PATHS.items():
            module_name, class_name = class_path.rsplit(".", 1)
            terrain_class = getattr(import_module(module_name), class_name)
            terrain_instances[terrain_name] = terrain_class()

    _OFFLINE_TERRAIN_INSTANCES = terrain_instances
    return terrain_instances


def _build_offline_resource_grid(mapgen: Any, *, width: int, height: int) -> dict[tuple[int, int], _OfflineRuntimeTileProxy]:
    ensure_offline_worldgen_bootstrap()

    with _temporary_working_directory(SCIV_ROOT):
        from gameplay.resource import Resources

        terrain_instances = _load_offline_terrain_instances()
        resource_grid: dict[tuple[int, int], _OfflineRuntimeTileProxy] = {}

        for col in range(height):
            for row in range(width):
                hex_tile = mapgen.hex_grid.grid[col][row]
                terrain_name = getattr(hex_tile, "terrain", None)
                if not isinstance(terrain_name, str) or terrain_name not in terrain_instances:
                    raise ValueError(f"Unsupported offline terrain '{terrain_name}' while building resource preview grid.")

                terrain = terrain_instances[terrain_name]
                resource_grid[(col, row)] = _OfflineRuntimeTileProxy(
                    x=int(col),
                    y=int(row),
                    is_water=bool(hex_tile.is_water),
                    is_coast=bool(getattr(hex_tile, "is_coast", False)),
                    raw_hex=hex_tile,
                    terrain=terrain,
                    resources=Resources(),
                    passable=bool(getattr(terrain, "passable", True)),
                )

    return resource_grid


def _allocate_offline_resources(mapgen: Any, *, width: int, height: int) -> None:
    ensure_offline_worldgen_bootstrap()

    with _temporary_working_directory(SCIV_ROOT):
        from gameplay.repositories.resources import ResourceRepository
        from gameplay.resource import ResourceType
        from system.generators.resource_allocator import ResourceAllocator

        resource_grid = _build_offline_resource_grid(mapgen, width=width, height=height)
        resource_classes = ResourceRepository.all_by_type(
            [ResourceType.STRATEGIC, ResourceType.BONUS, ResourceType.LUXURY]
        )
        if not resource_grid or not resource_classes:
            return

        allocator = ResourceAllocator(resource_grid, list(resource_classes))
        allocator.allocate_resources()


def _serialize_runtime_resource_key(hex_tile: Any) -> str | None:
    resource = hex_tile.get_gameplay_resource()
    if resource is None:
        return None
    return getattr(resource, "key", getattr(resource, "__name__", None))


def _build_dynamic_runtime_region_maps(
    mapgen: Any,
    *,
    seed: int,
    visible_coords: set[tuple[int, int]],
) -> tuple[dict[tuple[int, int], dict[str, Any]], dict[tuple[int, int], dict[str, Any]], dict[tuple[int, int], dict[str, Any]]]:
    from system.generators.dynamic_worlds.biomes import build_named_biome_regions
    from system.generators.dynamic_worlds.landmasses import build_named_landmasses
    from system.generators.dynamic_worlds.rivers import build_named_rivers

    landmass_data: dict[tuple[int, int], dict[str, Any]] = {}
    biome_region_data: dict[tuple[int, int], dict[str, Any]] = {}
    river_data: dict[tuple[int, int], dict[str, Any]] = {}

    for landmass in build_named_landmasses(mapgen.geoforms, seed=seed, visible_coords=visible_coords):
        for coord in landmass.tiles:
            landmass_data[coord] = {
                "landmass_name": landmass.name,
                "landmass_type": landmass.kind,
            }

    for region in build_named_biome_regions(mapgen.hex_grid, seed=seed, visible_coords=visible_coords):
        for coord in region.tiles:
            biome_region_data[coord] = {
                "biome_region_name": region.name,
                "biome_region_type": region.biome_title,
            }

    for river in build_named_rivers(mapgen.rivers_sources, seed=seed, visible_coords=visible_coords):
        for coord in river.tiles:
            current = river_data.setdefault(coord, {"river_names": []})
            river_names = current.setdefault("river_names", [])
            river_names.append(river.name)

    for current in river_data.values():
        river_names = list(current.get("river_names", []))
        current["river_names"] = river_names
        current["primary_river_name"] = river_names[0] if river_names else None

    return landmass_data, biome_region_data, river_data


def _build_offline_runtime_tiles(
    mapgen: Any,
    generator_spec: OfflineGeneratorSpec,
    *,
    width: int,
    height: int,
    seed: int,
) -> dict[str, JsonDict]:
    from system.subsystems.hexgen.enums import GeoformType

    visible_coords = {(col, row) for col in range(height) for row in range(width)}
    landmass_data: dict[tuple[int, int], dict[str, Any]] = {}
    biome_region_data: dict[tuple[int, int], dict[str, Any]] = {}
    river_data: dict[tuple[int, int], dict[str, Any]] = {}

    if generator_spec.name == "Dynamic Worlds":
        landmass_data, biome_region_data, river_data = _build_dynamic_runtime_region_maps(
            mapgen,
            seed=seed,
            visible_coords=visible_coords,
        )

    runtime_tiles: dict[str, JsonDict] = {}
    for col in range(height):
        for row in range(width):
            hex_tile = mapgen.hex_grid.grid[col][row]
            coord = (col, row)
            geoform_type = getattr(hex_tile, "geoform_type", None)

            tile_payload: JsonDict = {
                "x": int(col),
                "y": int(row),
                "altitude": float(hex_tile.altitude),
                "temperature": round(float(hex_tile.base_temperature[0]), 2),
                "moisture": float(hex_tile.moisture),
                "terrain": _terrain_name_to_runtime_key(getattr(hex_tile, "terrain", None)),
                "is_water": bool(hex_tile.is_water),
                "is_land": bool(hex_tile.is_land),
                "is_coast": bool(getattr(hex_tile, "is_coast", False)),
                "is_sea": bool(geoform_type in (GeoformType.sea, GeoformType.ocean)),
                "is_lake": bool(geoform_type == GeoformType.lake),
                "geoform_type": getattr(geoform_type, "name", str(geoform_type) if geoform_type is not None else None),
                "features": [str(feature) for feature in getattr(hex_tile, "features", ())],
                "resource": _serialize_runtime_resource_key(hex_tile),
                "landmass_name": None,
                "landmass_type": None,
                "biome_region_name": None,
                "biome_region_type": None,
                "river_names": [],
                "primary_river_name": None,
            }
            tile_payload.update(landmass_data.get(coord, {}))
            tile_payload.update(biome_region_data.get(coord, {}))
            tile_payload.update(river_data.get(coord, {}))
            runtime_tiles[f"{col}, {row}"] = tile_payload

    return runtime_tiles


def build_world(
    generator_spec: OfflineGeneratorSpec,
    *,
    width: int,
    height: int,
    seed: int,
    options: dict[str, Any],
    debug: bool,
) -> tuple[Any, JsonDict, JsonDict]:
    with _temporary_working_directory(SCIV_ROOT):
        from system.generators.dynamic_worlds.mapgen import DynamicMapGen
        from system.generators.dynamic_worlds.profiles import build_dynamic_map_params
        from system.generators.map_params import build_basic_map_params
        from system.subsystems.hexgen.mapgen import MapGen

        base_params = build_basic_map_params(width, height, seed=seed)

        if generator_spec.name == "Dynamic Worlds":
            map_params = build_dynamic_map_params(
                base_params,
                map_script=str(options.get("map_script", "continents")),
                biome_style=str(options.get("biome_style", "balanced")),
                world_age=str(options.get("world_age", "standard")),
                temperature=str(options.get("temperature", "temperate")),
                humidity=str(options.get("humidity", "normal")),
                sea_level=str(options.get("sea_level", "normal")),
                ocean_connectivity=str(options.get("ocean_connectivity", "natural")),
                river_amount=str(options.get("river_amount", "normal")),
                river_length=str(options.get("river_length", "normal")),
                tributaries=str(options.get("tributaries", "normal")),
                river_network=str(options.get("river_network", "natural")),
            )
            mapgen = DynamicMapGen(
                map_params,
                map_script=str(options.get("map_script", "continents")),
                biome_style=str(options.get("biome_style", "balanced")),
                debug=debug,
            )
        else:
            map_params = base_params
            mapgen = MapGen(map_params, debug=debug)

    world_stats = {
        "seed": seed,
        "map_size": [width, height],
        "generator_profiles": json_ready(options),
    }
    return mapgen, map_params, world_stats


def generate_world_payload(
    generator_spec: OfflineGeneratorSpec,
    *,
    width: int,
    height: int,
    seed: int,
    options: dict[str, Any],
    debug: bool,
    source: str,
    extra_meta: JsonDict | None = None,
    world_generation_stats: JsonDict | None = None,
    progress_callback: ProgressCallback | None = None,
) -> JsonDict:
    total_steps = 5

    _report_progress(
        progress_callback,
        step=1,
        total=total_steps,
        message="Building raw world",
    )
    mapgen, map_params, generated_stats = build_world(
        generator_spec,
        width=width,
        height=height,
        seed=seed,
        options=options,
        debug=debug,
    )

    _report_progress(
        progress_callback,
        step=2,
        total=total_steps,
        message="Preparing terrain preview",
    )
    _prepare_offline_hexes_for_export(
        mapgen,
        generator_spec,
        width=width,
        height=height,
        options=options,
    )

    _report_progress(
        progress_callback,
        step=3,
        total=total_steps,
        message="Allocating runtime resources",
    )
    _allocate_offline_resources(
        mapgen,
        width=width,
        height=height,
    )

    _report_progress(
        progress_callback,
        step=4,
        total=total_steps,
        message="Building runtime preview",
    )
    runtime_tiles = _build_offline_runtime_tiles(
        mapgen,
        generator_spec,
        width=width,
        height=height,
        seed=seed,
    )

    merged_stats = dict(generated_stats)
    if world_generation_stats is not None:
        merged_stats.update(world_generation_stats)

    with _temporary_working_directory(SCIV_ROOT):
        from system.generators.debug_export import build_raw_world_payload

        _report_progress(
            progress_callback,
            step=5,
            total=total_steps,
            message="Serializing world dump",
        )
        return build_raw_world_payload(
            mapgen=mapgen,
            generator_name=generator_spec.name,
            generator_class=generator_spec.class_path,
            requested_width=width,
            requested_height=height,
            seed=seed,
            setup_options=json_ready(options),
            map_params=map_params,
            source=source,
            world_generation_stats=merged_stats,
            runtime_tiles=runtime_tiles,
            extra_meta=extra_meta,
        )


def write_world_payload(payload: JsonDict, *, export_dir: str, file_stem: str) -> Path:
    with _temporary_working_directory(SCIV_ROOT):
        from system.generators.debug_export import write_worldgen_export

        return write_worldgen_export(
            payload,
            export_dir=export_dir,
            file_stem=file_stem,
        )


def _load_fallback_config_manager() -> _FallbackConfigManager:
    sample_path = SCIV_ROOT / "config_sample.json"
    export_dir = "sciv/debugging/worldgen"
    batch_count = 4

    try:
        with sample_path.open("r", encoding="utf-8") as fp:
            payload = json.load(fp)
        debug_payload = payload.get("debug") if isinstance(payload, dict) else {}
        export_payload = debug_payload.get("world_generation_export") if isinstance(debug_payload, dict) else {}

        configured_dir = export_payload.get("output_dir") if isinstance(export_payload, dict) else None
        if isinstance(configured_dir, str) and configured_dir.strip():
            export_dir = configured_dir.strip()

        configured_count = export_payload.get("offline_batch_count") if isinstance(export_payload, dict) else None
        if isinstance(configured_count, int) and configured_count > 0:
            batch_count = configured_count
    except Exception:
        pass

    return _FallbackConfigManager(export_dir=export_dir, batch_count=batch_count)
