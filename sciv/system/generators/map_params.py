from typing import Any

from system.subsystems.hexgen.enums import MapType, OceanType


def build_basic_map_params(width: int, height: int, *, seed: int | None) -> dict[str, Any]:
    number_of_tiles = width * height

    return {
        "map_type": MapType.terran,
        "surface_pressure": 1013.25,
        "size": max(width, height),
        "year_length": 365,
        "day_length": 24,
        "base_temp": 0,
        "avg_temp": 12.5,
        "sea_percent": 55,
        "hydrosphere": True,
        "ocean_type": [OceanType.water],
        "random_seed": seed,
        "roughness": 17,
        "height_range": (0, 240),
        "pressure": 1,
        "axial_tilt": 18,
        "craters": True,
        "volcanoes": True,
        "volcano_area_size": 1,
        "num_volcanoes": max(1, number_of_tiles // 2000),
        "num_rivers": number_of_tiles // 400,
        "num_territories": number_of_tiles // 300,
        "lake_to_sea_tiles": 100,
        "sea_to_ocean_tiles": 150,
        "force_connected_oceans": False,
    }
