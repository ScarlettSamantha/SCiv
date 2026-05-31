from dataclasses import replace
from typing import Any

from gameplay.founding.site_scoring import TileScoringProfile, resolve_tile_scoring_profile
from system.generators.dynamic_worlds.models import DynamicOptionProfile

LANDMASS_PROFILES: dict[str, DynamicOptionProfile] = {
    "continents": DynamicOptionProfile(
        key="continents",
        name="Continents",
        description="Balanced multi-continent worlds with inland expansion room and stable coastlines.",
        params={
            "sea_percent": 55,
            "roughness": 18,
            "num_rivers_factor": 1.0,
            "num_territories_factor": 1.0,
            "lake_to_sea_tiles": 90,
            "sea_to_ocean_tiles": 150,
            "hadley_strength": 0.8,
            "river_source_spacing": 7,
            "channel_count": 1,
            "channel_depth": 56.0,
            "channel_width_ratio": 0.042,
            "inland_sea_count": 1,
            "inland_sea_depth": 50.0,
            "inland_sea_radius_ratio": 0.10,
            "tributary_factor": 0.45,
            "river_connector_factor": 0.24,
            "river_connector_radius": 10,
            "river_distributary_factor": 0.18,
            "river_distributary_radius": 6,
            "river_valley_depth": 4.8,
            "river_valley_radius": 2,
            "height_smoothing_passes": 2,
            "height_smoothing_strength": 0.26,
            "mountain_knee_ratio": 0.79,
            "mountain_compression_ratio": 0.50,
        },
    ),
    "pangaea": DynamicOptionProfile(
        key="pangaea",
        name="Pangaea",
        description="Large central supercontinents with broader inland starts and fewer fragmented shorelines.",
        params={
            "sea_percent": 44,
            "roughness": 15,
            "num_rivers_factor": 1.2,
            "num_territories_factor": 0.9,
            "lake_to_sea_tiles": 110,
            "sea_to_ocean_tiles": 220,
            "hadley_strength": 0.7,
            "river_source_spacing": 8,
            "channel_count": 1,
            "channel_depth": 68.0,
            "channel_width_ratio": 0.038,
            "inland_sea_count": 1,
            "inland_sea_depth": 60.0,
            "inland_sea_radius_ratio": 0.12,
            "tributary_factor": 0.55,
            "river_connector_factor": 0.34,
            "river_connector_radius": 12,
            "river_distributary_factor": 0.24,
            "river_distributary_radius": 7,
            "river_valley_depth": 5.8,
            "river_valley_radius": 2,
            "height_smoothing_passes": 2,
            "height_smoothing_strength": 0.26,
            "mountain_knee_ratio": 0.79,
            "mountain_compression_ratio": 0.50,
        },
    ),
    "small_continents": DynamicOptionProfile(
        key="small_continents",
        name="Small Continents",
        description="Medium fractured landmasses that still preserve strong coast-heavy expansion routes.",
        params={
            "sea_percent": 59,
            "roughness": 19,
            "num_rivers_factor": 1.05,
            "num_territories_factor": 1.15,
            "lake_to_sea_tiles": 70,
            "sea_to_ocean_tiles": 125,
            "hadley_strength": 0.82,
            "river_source_spacing": 6,
            "channel_count": 2,
            "channel_depth": 54.0,
            "channel_width_ratio": 0.034,
            "inland_sea_count": 1,
            "inland_sea_depth": 42.0,
            "inland_sea_radius_ratio": 0.08,
            "tributary_factor": 0.40,
            "river_connector_factor": 0.22,
            "river_connector_radius": 9,
            "river_distributary_factor": 0.16,
            "river_distributary_radius": 6,
            "river_valley_depth": 4.4,
            "river_valley_radius": 2,
            "height_smoothing_passes": 2,
            "height_smoothing_strength": 0.24,
            "mountain_knee_ratio": 0.81,
            "mountain_compression_ratio": 0.56,
        },
    ),
    "archipelago": DynamicOptionProfile(
        key="archipelago",
        name="Archipelago",
        description="Island chains, tight channels, and coastal starts with lighter river spacing pressure.",
        params={
            "sea_percent": 68,
            "roughness": 21,
            "num_rivers_factor": 0.85,
            "num_territories_factor": 1.35,
            "lake_to_sea_tiles": 45,
            "sea_to_ocean_tiles": 90,
            "hadley_strength": 0.88,
            "river_source_spacing": 4,
            "channel_count": 2,
            "channel_depth": 38.0,
            "channel_width_ratio": 0.030,
            "inland_sea_count": 0,
            "inland_sea_depth": 0.0,
            "inland_sea_radius_ratio": 0.0,
            "tributary_factor": 0.22,
            "river_connector_factor": 0.12,
            "river_connector_radius": 7,
            "river_distributary_factor": 0.08,
            "river_distributary_radius": 5,
            "river_valley_depth": 3.5,
            "river_valley_radius": 1,
            "height_smoothing_passes": 1,
            "height_smoothing_strength": 0.20,
            "mountain_knee_ratio": 0.85,
            "mountain_compression_ratio": 0.68,
        },
    ),
    "fractal": DynamicOptionProfile(
        key="fractal",
        name="Fractal",
        description="Jagged, irregular coastlines with varied inland pockets and mixed-sized landmasses.",
        params={
            "sea_percent": 57,
            "roughness": 23,
            "num_rivers_factor": 1.1,
            "num_territories_factor": 1.25,
            "lake_to_sea_tiles": 85,
            "sea_to_ocean_tiles": 135,
            "hadley_strength": 0.84,
            "river_source_spacing": 5,
            "channel_count": 2,
            "channel_depth": 60.0,
            "channel_width_ratio": 0.040,
            "inland_sea_count": 1,
            "inland_sea_depth": 46.0,
            "inland_sea_radius_ratio": 0.09,
            "tributary_factor": 0.65,
            "river_connector_factor": 0.30,
            "river_connector_radius": 10,
            "river_distributary_factor": 0.28,
            "river_distributary_radius": 7,
            "river_valley_depth": 5.2,
            "river_valley_radius": 2,
            "height_smoothing_passes": 2,
            "height_smoothing_strength": 0.27,
            "mountain_knee_ratio": 0.80,
            "mountain_compression_ratio": 0.52,
        },
    ),
}

BIOME_STYLE_PROFILES: dict[str, DynamicOptionProfile] = {
    "balanced": DynamicOptionProfile(
        key="balanced",
        name="Balanced",
        description="Keeps the current climate mix while letting temperature and humidity do the fine tuning.",
        params={
            "equatorial_moisture_bonus": 0.9,
            "subtropical_dryness_bonus": 0.8,
            "polar_moisture_bonus": 0.2,
            "rain_shadow_multiplier": 1.0,
            "coastal_moisture_bonus": 0.35,
            "river_moisture_bonus": 0.3,
            "score_overrides": {},
        },
    ),
    "verdant": DynamicOptionProfile(
        key="verdant",
        name="Verdant",
        description="Biases toward greener belts, denser rivers, and lower desert pressure.",
        params={
            "desert_delta": -0.03,
            "steppe_delta": -0.02,
            "num_rivers_factor": 1.15,
            "coast_decay_delta": 0.3,
            "rain_shadow_delta": -0.2,
            "equatorial_moisture_bonus": 1.35,
            "subtropical_dryness_bonus": 0.45,
            "polar_moisture_bonus": 0.35,
            "rain_shadow_multiplier": 0.8,
            "coastal_moisture_bonus": 0.55,
            "river_moisture_bonus": 0.5,
            "score_overrides": {
                "food_weight": 2.15,
                "river_bonus": 3.9,
                "freshwater_bonus": 1.9,
            },
        },
    ),
    "arid": DynamicOptionProfile(
        key="arid",
        name="Arid",
        description="Pushes drier interiors, wider desert transitions, and more meaningful freshwater belts.",
        params={
            "avg_temp_delta": 2,
            "equator_temp_delta": 2.0,
            "pole_temp_delta": 1.0,
            "desert_delta": 0.05,
            "steppe_delta": 0.04,
            "num_rivers_factor": 0.8,
            "coast_decay_delta": -0.3,
            "hadley_delta": 0.05,
            "rain_shadow_delta": 0.35,
            "river_source_spacing_delta": 1,
            "equatorial_moisture_bonus": 0.55,
            "subtropical_dryness_bonus": 1.35,
            "polar_moisture_bonus": 0.15,
            "rain_shadow_multiplier": 1.3,
            "coastal_moisture_bonus": 0.15,
            "river_moisture_bonus": 0.4,
            "score_overrides": {
                "food_weight": 1.9,
                "production_weight": 1.95,
                "river_bonus": 4.4,
                "freshwater_bonus": 2.3,
            },
        },
    ),
    "frigid": DynamicOptionProfile(
        key="frigid",
        name="Frigid",
        description="Pulls the climate colder, stretches tundra belts, and slightly rewards harsher but productive starts.",
        params={
            "base_temp_delta": -6,
            "avg_temp_delta": -5,
            "equator_temp_delta": -4.0,
            "pole_temp_delta": -8.0,
            "desert_delta": -0.04,
            "steppe_delta": 0.01,
            "num_rivers_factor": 0.9,
            "coast_decay_delta": 0.1,
            "rain_shadow_delta": -0.15,
            "equatorial_moisture_bonus": 0.4,
            "subtropical_dryness_bonus": 0.5,
            "polar_moisture_bonus": 0.85,
            "rain_shadow_multiplier": 0.95,
            "coastal_moisture_bonus": 0.3,
            "river_moisture_bonus": 0.25,
            "score_overrides": {
                "production_weight": 2.0,
                "freshwater_bonus": 1.8,
                "hill_bonus": 0.9,
            },
        },
    ),
}

RIVER_AMOUNT_CHOICES: tuple[tuple[str, str], ...] = (
    ("Sparse", "sparse"),
    ("Normal", "normal"),
    ("Plentiful", "plentiful"),
)

RIVER_AMOUNT_FACTORS: dict[str, float] = {
    "sparse": 0.7,
    "normal": 1.0,
    "plentiful": 1.35,
}

RIVER_LENGTH_CHOICES: tuple[tuple[str, str], ...] = (
    ("Short", "short"),
    ("Normal", "normal"),
    ("Long", "long"),
)

RIVER_LENGTH_ADJUSTMENTS: dict[str, dict[str, int]] = {
    "short": {
        "river_source_spacing_delta": -1,
        "river_source_min_distance_delta": -1,
    },
    "normal": {
        "river_source_spacing_delta": 0,
        "river_source_min_distance_delta": 0,
    },
    "long": {
        "river_source_spacing_delta": 1,
        "river_source_min_distance_delta": 2,
    },
}

TRIBUTARY_CHOICES: tuple[tuple[str, str], ...] = (
    ("Few", "few"),
    ("Normal", "normal"),
    ("Many", "many"),
)

TRIBUTARY_FACTORS: dict[str, float] = {
    "few": 0.6,
    "normal": 1.0,
    "many": 1.6,
}

RIVER_NETWORK_CHOICES: tuple[tuple[str, str], ...] = (
    ("Simple", "simple"),
    ("Natural", "natural"),
    ("Braided", "braided"),
)

OCEAN_CONNECTIVITY_CHOICES: tuple[tuple[str, str], ...] = (
    ("Natural", "natural"),
    ("Connected Main Oceans", "connected"),
)

RIVER_NETWORK_ADJUSTMENTS: dict[str, dict[str, float]] = {
    "simple": {
        "connector_factor": 0.55,
        "connector_radius_delta": -1.0,
        "distributary_factor": 0.5,
        "distributary_radius_delta": -1.0,
    },
    "natural": {
        "connector_factor": 1.0,
        "connector_radius_delta": 0.0,
        "distributary_factor": 1.0,
        "distributary_radius_delta": 0.0,
    },
    "braided": {
        "connector_factor": 1.6,
        "connector_radius_delta": 2.0,
        "distributary_factor": 1.8,
        "distributary_radius_delta": 1.0,
    },
}

WORLD_AGE_PRESETS: dict[str, dict[str, Any]] = {
    "young": {
        "roughness_delta": 3,
        "height_range": (0, 255),
        "num_volcanoes_factor": 1.4,
        "volcano_area_size": 1,
    },
    "standard": {
        "roughness_delta": 0,
        "height_range": (0, 245),
        "num_volcanoes_factor": 1.0,
        "volcano_area_size": 1,
    },
    "old": {
        "roughness_delta": -4,
        "height_range": (0, 232),
        "num_volcanoes_factor": 0.65,
        "volcano_area_size": 1,
    },
}

TEMPERATURE_PRESETS: dict[str, dict[str, Any]] = {
    "cool": {"base_temp": -8, "avg_temp": 8, "equator_temp": 23.0, "pole_temp": -28.0},
    "temperate": {"base_temp": 0, "avg_temp": 13, "equator_temp": 28.0, "pole_temp": -20.0},
    "hot": {"base_temp": 6, "avg_temp": 19, "equator_temp": 34.0, "pole_temp": -12.0},
}

HUMIDITY_PRESETS: dict[str, dict[str, Any]] = {
    "arid": {
        "num_rivers_factor": 0.7,
        "desert_target_ratio": 0.18,
        "steppe_target_ratio": 0.13,
        "coast_decay": 2.0,
    },
    "normal": {
        "num_rivers_factor": 1.0,
        "desert_target_ratio": 0.12,
        "steppe_target_ratio": 0.10,
        "coast_decay": 2.5,
    },
    "wet": {
        "num_rivers_factor": 1.35,
        "desert_target_ratio": 0.08,
        "steppe_target_ratio": 0.08,
        "coast_decay": 3.1,
    },
}

SEA_LEVEL_ADJUSTMENTS: dict[str, int] = {"low": -8, "normal": 0, "high": 8}

LANDMASS_FORWARD_KEYS = (
    "channel_count",
    "channel_depth",
    "channel_width_ratio",
    "height_smoothing_passes",
    "height_smoothing_strength",
    "inland_sea_count",
    "inland_sea_depth",
    "inland_sea_radius_ratio",
    "mountain_compression_ratio",
    "mountain_knee_ratio",
    "river_connector_factor",
    "river_connector_radius",
    "river_distributary_factor",
    "river_distributary_radius",
    "tributary_factor",
    "river_valley_depth",
    "river_valley_radius",
)

BIOME_FORWARD_KEYS = (
    "equatorial_moisture_bonus",
    "subtropical_dryness_bonus",
    "polar_moisture_bonus",
    "rain_shadow_multiplier",
    "coastal_moisture_bonus",
    "river_moisture_bonus",
)


def landmass_choices() -> tuple[tuple[str, str], ...]:
    return tuple((profile.name, key) for key, profile in LANDMASS_PROFILES.items())


def biome_style_choices() -> tuple[tuple[str, str], ...]:
    return tuple((profile.name, key) for key, profile in BIOME_STYLE_PROFILES.items())


def river_amount_choices() -> tuple[tuple[str, str], ...]:
    return RIVER_AMOUNT_CHOICES


def river_length_choices() -> tuple[tuple[str, str], ...]:
    return RIVER_LENGTH_CHOICES


def tributary_choices() -> tuple[tuple[str, str], ...]:
    return TRIBUTARY_CHOICES


def river_network_choices() -> tuple[tuple[str, str], ...]:
    return RIVER_NETWORK_CHOICES


def ocean_connectivity_choices() -> tuple[tuple[str, str], ...]:
    return OCEAN_CONNECTIVITY_CHOICES


def get_landmass_profile_name(key: str) -> str:
    return LANDMASS_PROFILES.get(key, LANDMASS_PROFILES["continents"]).name


def get_biome_style_profile_name(key: str) -> str:
    return BIOME_STYLE_PROFILES.get(key, BIOME_STYLE_PROFILES["balanced"]).name


def build_dynamic_map_params(
    base_params: dict[str, Any],
    *,
    map_script: str,
    biome_style: str,
    world_age: str,
    temperature: str,
    humidity: str,
    sea_level: str,
    river_amount: str,
    river_length: str,
    tributaries: str,
    river_network: str,
    ocean_connectivity: str,
) -> dict[str, Any]:
    params = dict(base_params)

    landmass = LANDMASS_PROFILES.get(map_script, LANDMASS_PROFILES["continents"])
    biome = BIOME_STYLE_PROFILES.get(biome_style, BIOME_STYLE_PROFILES["balanced"])
    age = WORLD_AGE_PRESETS.get(world_age, WORLD_AGE_PRESETS["standard"])
    temp = TEMPERATURE_PRESETS.get(temperature, TEMPERATURE_PRESETS["temperate"])
    moisture = HUMIDITY_PRESETS.get(humidity, HUMIDITY_PRESETS["normal"])
    river_count_factor = RIVER_AMOUNT_FACTORS.get(river_amount, RIVER_AMOUNT_FACTORS["normal"])
    river_length_adjustment = RIVER_LENGTH_ADJUSTMENTS.get(river_length, RIVER_LENGTH_ADJUSTMENTS["normal"])
    tributary_factor = TRIBUTARY_FACTORS.get(tributaries, TRIBUTARY_FACTORS["normal"])
    river_network_adjustment = RIVER_NETWORK_ADJUSTMENTS.get(
        river_network,
        RIVER_NETWORK_ADJUSTMENTS["natural"],
    )

    params["sea_percent"] = _clamp_int(
        int(landmass.params["sea_percent"]) + SEA_LEVEL_ADJUSTMENTS.get(sea_level, 0),
        30,
        75,
    )
    params["roughness"] = max(8, int(landmass.params["roughness"]) + int(age["roughness_delta"]))
    params["height_range"] = age["height_range"]
    params["base_temp"] = int(temp["base_temp"]) + int(biome.params.get("base_temp_delta", 0))
    params["avg_temp"] = int(temp["avg_temp"]) + int(biome.params.get("avg_temp_delta", 0))
    params["equator_temp"] = float(temp["equator_temp"]) + float(biome.params.get("equator_temp_delta", 0.0))
    params["pole_temp"] = float(temp["pole_temp"]) + float(biome.params.get("pole_temp_delta", 0.0))
    params["desert_target_ratio"] = _clamp_float(
        float(moisture["desert_target_ratio"]) + float(biome.params.get("desert_delta", 0.0)),
        0.02,
        0.35,
    )
    params["steppe_target_ratio"] = _clamp_float(
        float(moisture["steppe_target_ratio"]) + float(biome.params.get("steppe_delta", 0.0)),
        0.02,
        0.25,
    )
    params["coast_decay"] = max(
        0.8,
        float(moisture["coast_decay"]) + float(biome.params.get("coast_decay_delta", 0.0)),
    )
    params["hadley_strength"] = max(
        0.3,
        float(landmass.params["hadley_strength"]) + float(biome.params.get("hadley_delta", 0.0)),
    )
    params["rain_shadow_strength"] = max(
        0.4,
        float(params.get("rain_shadow_strength", 1.6)) + float(biome.params.get("rain_shadow_delta", 0.0)),
    )
    params["lake_to_sea_tiles"] = int(landmass.params["lake_to_sea_tiles"])
    params["sea_to_ocean_tiles"] = int(landmass.params["sea_to_ocean_tiles"])
    params["volcano_area_size"] = int(age["volcano_area_size"])

    river_factor = (
        float(landmass.params["num_rivers_factor"])
        * float(moisture["num_rivers_factor"])
        * float(biome.params.get("num_rivers_factor", 1.0))
        * river_count_factor
    )
    territory_factor = float(landmass.params["num_territories_factor"])
    volcano_factor = float(age["num_volcanoes_factor"])

    params["num_rivers"] = max(1, int(params["num_rivers"] * river_factor))
    params["num_territories"] = max(1, int(params["num_territories"] * territory_factor))
    params["num_volcanoes"] = max(1, int(params["num_volcanoes"] * volcano_factor))
    params["river_source_spacing"] = max(
        2,
        int(landmass.params.get("river_source_spacing", params.get("river_source_spacing", 6)))
        + int(biome.params.get("river_source_spacing_delta", 0)),
    )

    for key in LANDMASS_FORWARD_KEYS:
        if key in landmass.params:
            params[key] = landmass.params[key]

    for key in BIOME_FORWARD_KEYS:
        if key in biome.params:
            params[key] = biome.params[key]

    params["river_source_spacing"] = max(
        2,
        int(params["river_source_spacing"]) + int(river_length_adjustment["river_source_spacing_delta"]),
    )
    default_source_min_distance = max(2, int(round(float(params["river_source_spacing"]) * 0.5)) or 2)
    params["river_source_min_distance"] = max(
        2,
        default_source_min_distance + int(river_length_adjustment["river_source_min_distance_delta"]),
    )
    if "tributary_factor" in params:
        params["tributary_factor"] = _clamp_float(float(params["tributary_factor"]) * tributary_factor, 0.0, 1.6)
    if "river_connector_factor" in params:
        params["river_connector_factor"] = _clamp_float(
            float(params["river_connector_factor"]) * float(river_network_adjustment["connector_factor"]),
            0.0,
            1.8,
        )
    if "river_distributary_factor" in params:
        params["river_distributary_factor"] = _clamp_float(
            float(params["river_distributary_factor"]) * float(river_network_adjustment["distributary_factor"]),
            0.0,
            1.6,
        )
    if "river_connector_radius" in params:
        params["river_connector_radius"] = max(
            4,
            int(round(float(params["river_connector_radius"]) + river_network_adjustment["connector_radius_delta"])),
        )
    if "river_distributary_radius" in params:
        params["river_distributary_radius"] = max(
            3,
            int(
                round(
                    float(params["river_distributary_radius"])
                    + river_network_adjustment["distributary_radius_delta"]
                )
            ),
        )

    params["force_connected_oceans"] = ocean_connectivity == "connected"

    return params


def get_dynamic_tile_scoring_profile(map_script: str, biome_style: str) -> TileScoringProfile:
    profile = resolve_tile_scoring_profile(map_script)

    if map_script == "archipelago":
        profile = replace(profile, bay_bonus=1.1, strait_bonus=1.0, island_bonus=1.6)
    elif map_script == "small_continents":
        profile = replace(profile, island_bonus=1.25, coast_bonus=5.6, water_penalty_scale=0.65)
    elif map_script == "fractal":
        profile = replace(profile, bay_bonus=1.15, strait_bonus=1.1, peninsula_bonus=1.2)
    elif map_script == "pangaea":
        profile = replace(profile, expansion_bonus_scale=1.45, edge_penalty_scale=1.2, coast_bonus_scale=0.55)

    biome_profile = BIOME_STYLE_PROFILES.get(biome_style, BIOME_STYLE_PROFILES["balanced"])
    overrides = biome_profile.params.get("score_overrides", {})
    if overrides:
        profile = replace(profile, **overrides)

    return profile


def _clamp_int(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))


def _clamp_float(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
