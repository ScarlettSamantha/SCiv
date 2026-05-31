"""Color and layer helper utilities for the standalone worldgen viewer."""

import hashlib

from PyQt6.QtGui import QColor

from worldgen_viewer_support import HexRecord, WorldgenDump, resource_display_text, terrain_display_name


MAX_TERRITORY_LEGEND_ITEMS = 8
MAX_RESOURCE_LEGEND_ITEMS = 18
MAX_OVERLAY_SUMMARY_ITEMS = 12
BIOME_COLORS = {
    "arctic": QColor("#b6d6ff"),
    "desert": QColor("#d8c07a"),
    "frozen": QColor("#d9f1ff"),
    "grasslands": QColor("#8dbb5a"),
    "jungle": QColor("#2f8f4e"),
    "plains": QColor("#b8c16d"),
    "savannah": QColor("#b6a25e"),
    "swamp": QColor("#4f7d59"),
    "taiga": QColor("#6f9c7d"),
    "tundra": QColor("#9ab5ad"),
}
GEOFORM_COLORS = {
    "continent": QColor("#5d8c46"),
    "island": QColor("#93b86b"),
    "islet": QColor("#c8d5a3"),
    "lake": QColor("#4b89c8"),
    "ocean": QColor("#2b4f7f"),
    "sea": QColor("#34669c"),
}
TERRAIN_COLORS = {
    "coast": QColor("#4e9cc9"),
    "desert": QColor("#c6b46f"),
    "forest": QColor("#5a8d4e"),
    "grasslands": QColor("#7aac55"),
    "hills": QColor("#92775a"),
    "jungle": QColor("#2f8f4e"),
    "lake": QColor("#5d97c7"),
    "mountains": QColor("#8d8c92"),
    "ocean": QColor("#2f507c"),
    "plains": QColor("#9eaf66"),
    "savannah": QColor("#b6a25e"),
    "scrubland": QColor("#9fa65d"),
    "sea_ice": QColor("#dbeeff"),
    "snow": QColor("#edf6ff"),
    "tundra": QColor("#a8b5b0"),
    "volcano": QColor("#b85b47"),
}
RIVER_COLORS = {
    "Headwaters": QColor("#88f1c2"),
    "River braid": QColor("#79ddff"),
    "River connector": QColor("#5eafff"),
    "River channel": QColor("#4fc3f7"),
    "River confluence": QColor("#1eb5ff"),
    "River mouth": QColor("#9fe8ff"),
    "Land without river": QColor("#5d6c50"),
    "Water without river": QColor("#24394f"),
}
LABEL_COLORS = {
    "landmasses": QColor("#f2f1c2"),
    "biome_regions": QColor("#d1f0d7"),
    "rivers": QColor("#9ed2ff"),
}
RESOURCE_SPECIAL_COLORS = {
    "No resource": QColor("#6d7278"),
    "Outside runtime bounds": QColor("#42454f"),
}
OVERLAY_BUCKET_ORDER = {
    "biome": (
        "Ocean / deep sea",
        "Coast / shallow water",
        "Lake",
        "Sea ice",
        "Arctic",
        "Desert",
        "Frozen",
        "Grasslands",
        "Jungle",
        "Plains",
        "Savannah",
        "Swamp",
        "Taiga",
        "Tundra",
    ),
    "altitude": ("Deep water", "Shallow water", "Low land", "High land", "Peaks"),
    "moisture": ("Dry", "Balanced", "Wet"),
    "resources": ("No resource", "Outside runtime bounds"),
    "rivers": (
        "Headwaters",
        "River braid",
        "River connector",
        "River channel",
        "River confluence",
        "River mouth",
        "Land without river",
        "Water without river",
    ),
    "visibility": ("Visible runtime land", "Visible runtime water", "Outside runtime bounds"),
}


def _stable_color(key: str, saturation: int = 130, value: int = 190) -> QColor:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    hue = int.from_bytes(digest[:2], "big") % 360
    return QColor.fromHsv(hue, saturation, value)


def _water_color_from_kind(kind: str) -> QColor:
    if kind == "coast":
        return QColor("#5aaed6")
    if kind == "lake":
        return QColor("#5d97c7")
    if kind == "sea_ice":
        return QColor("#dbeeff")
    return QColor("#2f507c")


def _water_color_for_record(record: HexRecord) -> QColor:
    terrain_key = (record.terrain or "").lower()
    if terrain_key == "coast" or record.is_coast_water:
        return _water_color_from_kind("coast")
    if terrain_key == "lake" or record.geoform_type == "lake":
        return _water_color_from_kind("lake")
    if terrain_key == "seaice":
        return _water_color_from_kind("sea_ice")
    return _water_color_from_kind("ocean")


def _overlay_water_label(record: HexRecord) -> str:
    terrain_key = (record.terrain or "").lower()
    if terrain_key == "seaice":
        return "Sea ice"
    if terrain_key == "lake" or record.geoform_type == "lake":
        return "Lake"
    if terrain_key == "coast" or record.is_coast_water:
        return "Coast / shallow water"
    return "Ocean / deep sea"


def _altitude_bucket_label(dump: WorldgenDump, record: HexRecord) -> str:
    low, high = dump.altitude_range
    sealevel = _heightmap_sealevel(dump)
    low_land = min(high, max(low, sealevel + 6.0))
    mid_land = (low_land + high) / 2 if high > low_land else high
    deep_water_cutoff = (low + sealevel) / 2
    high_land_cutoff = (mid_land + high) / 2 if high > mid_land else high

    if record.is_water:
        return "Deep water" if record.altitude <= deep_water_cutoff else "Shallow water"
    if record.altitude <= mid_land:
        return "Low land"
    if record.altitude <= high_land_cutoff:
        return "High land"
    return "Peaks"


def _moisture_bucket_label(dump: WorldgenDump, record: HexRecord) -> str:
    low, high = dump.moisture_range
    mid = (low + high) / 2
    dry_cutoff = (low + mid) / 2
    wet_cutoff = (mid + high) / 2

    if record.moisture <= dry_cutoff:
        return "Dry"
    if record.moisture <= wet_cutoff:
        return "Balanced"
    return "Wet"


def _title_from_identifier(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").strip().title()


def _runtime_terrain_key(dump: WorldgenDump, record: HexRecord) -> str | None:
    runtime_tile = dump.runtime_tiles_by_coord.get(record.coord)
    terrain_value = runtime_tile.get("terrain") if runtime_tile is not None else None
    if isinstance(terrain_value, str) and terrain_value:
        return terrain_value
    return record.terrain


def _runtime_resource_key(dump: WorldgenDump, record: HexRecord) -> str | None:
    runtime_tile = dump.runtime_tiles_by_coord.get(record.coord)
    resource_value = runtime_tile.get("resource") if runtime_tile is not None else None
    return str(resource_value) if isinstance(resource_value, str) and resource_value else None


def _resource_label(dump: WorldgenDump, record: HexRecord) -> str:
    if not record.visible_in_runtime:
        return "Outside runtime bounds"

    resource_key = _runtime_resource_key(dump, record)
    if resource_key is None:
        return "No resource"

    return resource_display_text(resource_key) or resource_key


def _resource_color(dump: WorldgenDump, record: HexRecord) -> QColor:
    label = _resource_label(dump, record)
    special_color = RESOURCE_SPECIAL_COLORS.get(label)
    if special_color is not None:
        return QColor(special_color)

    resource_key = _runtime_resource_key(dump, record)
    return _stable_color(f"resource:{resource_key or label}", saturation=160, value=220)


def _runtime_terrain_label(dump: WorldgenDump, record: HexRecord) -> str:
    terrain_key = _runtime_terrain_key(dump, record)
    if terrain_key is None:
        if record.is_water:
            terrain_key = record.terrain or ""
            lowered = terrain_key.strip().lower().replace("_", "").replace("-", "")
            if lowered == "seaice":
                return "Sea ice / ice water"
            if lowered == "lake" or record.geoform_type == "lake":
                return "Lake"
            if lowered == "coast" or record.is_coast_water:
                return "Coast"
            return "Sea / ocean"
        return record.biome_title

    lowered = terrain_key.strip().lower().replace("_", "").replace("-", "")
    if lowered in {"sea", "ocean"}:
        return "Sea / ocean"
    if lowered == "seaice":
        return "Sea ice / ice water"

    return terrain_display_name(terrain_key) or _title_from_identifier(terrain_key)


def _runtime_terrain_color(dump: WorldgenDump, record: HexRecord) -> QColor:
    terrain_key = _runtime_terrain_key(dump, record)
    if terrain_key is None:
        return _water_color_for_record(record) if record.is_water else QColor(
            BIOME_COLORS.get(record.biome_key, _stable_color(record.biome_key))
        )

    lowered = terrain_key.strip().lower().replace("_", "").replace("-", "")
    if lowered == "coast":
        return QColor(TERRAIN_COLORS["coast"])
    if lowered == "lake":
        return QColor(TERRAIN_COLORS["lake"])
    if lowered == "seaice":
        return QColor(TERRAIN_COLORS["sea_ice"])
    if record.is_water or lowered in {"sea", "ocean"}:
        return QColor(TERRAIN_COLORS["ocean"])
    if "volcano" in lowered:
        return QColor(TERRAIN_COLORS["volcano"])

    land_color = _runtime_terrain_land_color(lowered, record)
    if "mountain" in lowered:
        return _blend(QColor(TERRAIN_COLORS["mountains"]), land_color, 0.36) if land_color is not None else QColor(
            TERRAIN_COLORS["mountains"]
        )
    if "hill" in lowered:
        return _blend(QColor(TERRAIN_COLORS["hills"]), land_color, 0.48) if land_color is not None else QColor(
            TERRAIN_COLORS["hills"]
        )
    if land_color is not None:
        return land_color

    return QColor(_stable_color(lowered))


def _runtime_terrain_land_color(lowered: str, record: HexRecord) -> QColor | None:
    if "ice" in lowered or "snow" in lowered:
        return QColor(TERRAIN_COLORS["snow"])
    if "tundra" in lowered:
        return QColor(TERRAIN_COLORS["tundra"])
    if "desert" in lowered:
        return QColor(TERRAIN_COLORS["desert"])
    if "jungle" in lowered:
        return QColor(TERRAIN_COLORS["jungle"])
    if "pineforest" in lowered or "heavyforest" in lowered or "forest" in lowered:
        return QColor(TERRAIN_COLORS["forest"])
    if "grass" in lowered:
        return QColor(TERRAIN_COLORS["grasslands"])
    if "savanna" in lowered:
        return QColor(TERRAIN_COLORS["savannah"])
    if "scrub" in lowered:
        return QColor(TERRAIN_COLORS["scrubland"])
    if "plain" in lowered:
        return QColor(TERRAIN_COLORS["plains"])

    biome_color = BIOME_COLORS.get(record.biome_key)
    return QColor(biome_color) if biome_color is not None else None


def _altitude_color(value: float, bounds: tuple[float, float], is_water: bool) -> QColor:
    low, high = bounds
    if high <= low:
        return QColor("#4c7aa8") if is_water else QColor("#7da261")

    normalized = max(0.0, min(1.0, (value - low) / (high - low)))
    if is_water:
        return _blend(QColor("#16314f"), QColor("#5ea3d4"), normalized)
    if normalized < 0.55:
        return _blend(QColor("#6c9b54"), QColor("#9f855c"), normalized / 0.55)
    return _blend(QColor("#9f855c"), QColor("#dfe5ea"), (normalized - 0.55) / 0.45)


def _moisture_color(value: float, bounds: tuple[float, float]) -> QColor:
    low, high = bounds
    if high <= low:
        return QColor("#7aa86a")

    normalized = max(0.0, min(1.0, (value - low) / (high - low)))
    if normalized < 0.5:
        return _blend(QColor("#c8a86a"), QColor("#6faa62"), normalized / 0.5)
    return _blend(QColor("#6faa62"), QColor("#4aa0c8"), (normalized - 0.5) / 0.5)


def _blend(first: QColor, second: QColor, amount: float) -> QColor:
    clamped = max(0.0, min(1.0, amount))
    red = round(first.red() + (second.red() - first.red()) * clamped)
    green = round(first.green() + (second.green() - first.green()) * clamped)
    blue = round(first.blue() + (second.blue() - first.blue()) * clamped)
    return QColor(red, green, blue)


def _heightmap_sealevel(dump: WorldgenDump) -> float:
    raw_payload = dump.raw_payload.get("raw") if isinstance(dump.raw_payload.get("raw"), dict) else {}
    heightmap = raw_payload.get("heightmap") if isinstance(raw_payload.get("heightmap"), dict) else {}
    sealevel = heightmap.get("sealevel")
    if isinstance(sealevel, int | float):
        return float(sealevel)

    low, high = dump.altitude_range
    return (low + high) / 2
