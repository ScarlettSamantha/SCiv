import random
from typing import Callable

from system.subsystems.hexgen.enums import GeoformType

LANDMASS_STARTS = (
    "al",
    "ar",
    "bel",
    "cal",
    "cor",
    "da",
    "el",
    "fal",
    "gal",
    "hal",
    "is",
    "ka",
    "lor",
    "mar",
    "na",
    "or",
    "pel",
    "qua",
    "rav",
    "sel",
    "tor",
    "ur",
    "val",
    "wyr",
)
LANDMASS_MIDDLES = ("a", "e", "i", "o", "u", "an", "en", "or", "ir", "el")
LANDMASS_ENDS = (
    "ria",
    "mere",
    "dor",
    "via",
    "ora",
    "ara",
    "en",
    "or",
    "eth",
    "une",
    "assa",
    "os",
)

LANDMASS_SUFFIXES: dict[GeoformType, tuple[str, ...]] = {
    GeoformType.continent: ("Continent", "Reach", "Expanse", "Crown"),
    GeoformType.large_island: ("Isle", "Island", "Reach", "Keys"),
    GeoformType.small_island: ("Cay", "Isle", "Atoll", "Key"),
    GeoformType.peninsula: ("Peninsula", "Spur", "Reach", "Cape"),
    GeoformType.isthmus: ("Isthmus", "Neck", "Bridge"),
}

BIOME_PATTERNS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "arctic": (("Frost", "Pale", "Winter", "Silent"), ("Ice", "Shelf", "Waste", "Reach")),
    "tundra": (("Frost", "Northwind", "Pale", "Cold"), ("Tundra", "Barrens", "Reach", "March")),
    "alpine_tundra": (("High", "Stone", "Frost", "Sky"), ("Heights", "Tundra", "Crown", "Spine")),
    "desert": (("Amber", "Sunscorched", "Ochre", "Burning"), ("Dunes", "Waste", "Sea", "Expanse")),
    "shrubland": (("Sage", "Dry", "Whispering", "Windworn"), ("Brush", "Heath", "Reach", "Scrub")),
    "savanna": (("Golden", "Lion", "Tall", "Dawn"), ("Savanna", "Grass", "Reach", "Steppe")),
    "grasslands": (("Verdant", "Green", "Golden", "Willow"), ("Plains", "Meadow", "Reach", "Prairie")),
    "boreal_forest": (("Pine", "North", "Deep", "Silent"), ("Forest", "Taiga", "Reach", "Wood")),
    "temperate_forest": (("Green", "Oak", "Moss", "Silver"), ("Forest", "Wood", "Grove", "March")),
    "temperate_rainforest": (("Misty", "Emerald", "Silver", "Rain"), ("Forest", "Canopy", "Wood", "Reach")),
    "tropical_forest": (("Jade", "Warm", "Parrot", "Blooming"), ("Jungle", "Forest", "Canopy", "Reach")),
    "tropical_rainforest": (("Verdant", "Jade", "Emerald", "Monsoon"), ("Rainforest", "Jungle", "Canopy", "Basin")),
}

RIVER_TITLES = ("River", "Run", "Wash", "Fork", "Flow")


def build_seeded_rng(seed: int | None, salt: str) -> random.Random:
    return random.Random(f"dynamic-worlds:{seed}:{salt}")


def generate_landmass_name(rng: random.Random, kind: GeoformType, used_names: set[str]) -> str:
    suffixes = LANDMASS_SUFFIXES.get(kind, (kind.title,))

    def builder() -> str:
        root = _build_root(rng)
        suffix = rng.choice(suffixes)
        if kind is GeoformType.continent and rng.random() < 0.35:
            return root
        if suffix in {"Continent", "Peninsula", "Isthmus"}:
            return f"{root} {suffix}"
        if suffix in {"Isle", "Cay", "Atoll", "Key"} and rng.random() < 0.4:
            return f"Isle of {root}"
        return f"{root} {suffix}"

    return _unique_name(used_names, builder)


def generate_biome_region_name(rng: random.Random, biome_key: str, biome_title: str, used_names: set[str]) -> str:
    adjectives, nouns = BIOME_PATTERNS.get(
        biome_key,
        (("Ancient", "Green", "Silent", "Wild"), (biome_title, "Reach", "Expanse", "March")),
    )

    def builder() -> str:
        if rng.random() < 0.55:
            return f"{rng.choice(adjectives)} {rng.choice(nouns)}"
        return f"{_build_root(rng)} {rng.choice(nouns)}"

    return _unique_name(used_names, builder)


def generate_river_name(rng: random.Random, used_names: set[str]) -> str:
    def builder() -> str:
        root = _build_root(rng)
        title = rng.choice(RIVER_TITLES)
        if title == "River":
            return f"River {root}"
        return f"{root} {title}"

    return _unique_name(used_names, builder)


def _build_root(rng: random.Random) -> str:
    parts = [rng.choice(LANDMASS_STARTS)]
    if rng.random() < 0.5:
        parts.append(rng.choice(LANDMASS_MIDDLES))
    parts.append(rng.choice(LANDMASS_ENDS))
    return "".join(parts).capitalize()


def _unique_name(used_names: set[str], builder: Callable[[], str]) -> str:
    for _ in range(24):
        candidate = builder()
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate

    suffix = 2
    while True:
        candidate = f"{builder()} {suffix}"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        suffix += 1
